"""Mini-Doctrine simulé en PHP pur, injecté avant le code de l'élève (RUN setup).

Fournit :
- Doctrine\\Common\\Collections\\{Collection, ArrayCollection}
- Doctrine\\ORM\\{EntityManagerInterface, FakeEntityManager}
- un EntityManager qui lit les attributs #[ORM\\...] par réflexion et affiche le SQL
  qu'enverrait Doctrine (INSERT / UPDATE / DELETE / SELECT), avec identity map,
  cascade persist, côté propriétaire, orphanRemoval et callbacks PrePersist/PreUpdate.
"""

DOCTRINE_SETUP = r"""
eval(<<<'PHPSIM'
namespace Doctrine\Common\Collections;

interface Collection extends \Countable, \IteratorAggregate, \ArrayAccess {
    public function add(mixed $element): void;
    public function removeElement(mixed $element): bool;
    public function contains(mixed $element): bool;
    public function toArray(): array;
    public function isEmpty(): bool;
    public function first(): mixed;
    public function filter(\Closure $p): Collection;
    public function map(\Closure $f): Collection;
}

class ArrayCollection implements Collection {
    private array $elements;
    public function __construct(array $elements = []) { $this->elements = $elements; }
    public function add(mixed $element): void { $this->elements[] = $element; }
    public function removeElement(mixed $element): bool {
        $k = array_search($element, $this->elements, true);
        if ($k === false) return false;
        unset($this->elements[$k]);
        $this->elements = array_values($this->elements);
        return true;
    }
    public function contains(mixed $element): bool { return in_array($element, $this->elements, true); }
    public function toArray(): array { return $this->elements; }
    public function isEmpty(): bool { return $this->elements === []; }
    public function first(): mixed { return $this->elements[0] ?? false; }
    public function filter(\Closure $p): Collection { return new ArrayCollection(array_values(array_filter($this->elements, $p))); }
    public function map(\Closure $f): Collection { return new ArrayCollection(array_map($f, $this->elements)); }
    public function count(): int { return count($this->elements); }
    public function getIterator(): \ArrayIterator { return new \ArrayIterator($this->elements); }
    public function offsetExists(mixed $o): bool { return isset($this->elements[$o]); }
    public function offsetGet(mixed $o): mixed { return $this->elements[$o] ?? null; }
    public function offsetSet(mixed $o, mixed $v): void { if ($o === null) $this->elements[] = $v; else $this->elements[$o] = $v; }
    public function offsetUnset(mixed $o): void { unset($this->elements[$o]); }
}

namespace Doctrine\DBAL\Types;

final class Types {
    const STRING = 'string'; const TEXT = 'text'; const INTEGER = 'integer'; const BOOLEAN = 'boolean';
    const DATE_IMMUTABLE = 'date_immutable'; const DATETIME_IMMUTABLE = 'datetime_immutable'; const JSON = 'json'; const DECIMAL = 'decimal';
}

namespace Doctrine\ORM;

class ORMException extends \RuntimeException {}

interface EntityManagerInterface {
    public function persist(object $entity): void;
    public function remove(object $entity): void;
    public function flush(): void;
    public function find(string $class, mixed $id): ?object;
}

final class FakeEntityManager implements EntityManagerInterface {
    /** Toutes les requêtes SQL "envoyées", dans l'ordre. */
    public array $log = [];
    /** Nombre de flush() qui ont réellement écrit en base (= transactions). */
    public int $transactions = 0;
    public bool $echo = true;
    private \SplObjectStorage $managed;     // objet suivi -> instantané
    private \SplObjectStorage $toInsert;
    private \SplObjectStorage $toDelete;
    private array $ids = [];                // table -> dernier id
    private array $db = [];                 // "class#id" -> objet en base pas encore chargé
    private array $identity = [];           // "class#id" -> objet chargé
    private array $meta = [];

    public function __construct() {
        $this->managed = new \SplObjectStorage();
        $this->toInsert = new \SplObjectStorage();
        $this->toDelete = new \SplObjectStorage();
    }

    // ---------- outils pour les exercices ----------
    /** Place un objet "en base" (avec un id), sans SQL : find() le chargera. */
    public function seed(object $e, ?int $id = null): object {
        $m = $this->meta($e::class);
        if ($m['id'] && $id !== null) $this->setVal($e, $m['id'], $id);
        $id = $this->getVal($e, $m['id']);
        if ($id === null) { $id = ++$this->ids[$m['table']]; $this->setVal($e, $m['id'], $id); }
        $this->ids[$m['table']] = max($this->ids[$m['table']] ?? 0, (int) $id);
        $this->db[$e::class . '#' . $id] = $e;
        return $e;
    }
    public function clearLog(): void { $this->log = []; $this->transactions = 0; }
    public function count(string $verb): int { return count(array_filter($this->log, fn($q) => str_starts_with($q, $verb))); }
    public function isManaged(object $e): bool { return $this->managed->contains($e); }

    // ---------- API Doctrine ----------
    public function persist(object $e): void {
        $this->meta($e::class);
        if ($this->managed->contains($e) || $this->toInsert->contains($e)) { $this->toDelete->detach($e); return; }
        $this->toInsert->attach($e);
        $this->cascade($e, 'persist');
    }
    public function remove(object $e): void {
        if ($this->toInsert->contains($e)) { $this->toInsert->detach($e); return; }
        if (!$this->managed->contains($e)) throw new ORMException('remove() : cet objet n\'est pas suivi par Doctrine (il ne vient pas de la base).');
        $this->toDelete->attach($e);
    }
    public function find(string $class, mixed $id): ?object {
        $k = $class . '#' . $id;
        if (isset($this->identity[$k])) return $this->identity[$k];
        $m = $this->meta($class);
        $this->sql('SELECT * FROM ' . $m['table'] . ' WHERE id = ' . $this->fmt($id));
        if (!isset($this->db[$k])) return null;
        $e = $this->db[$k];
        $this->identity[$k] = $e;
        $this->managed[$e] = $this->snapshot($e);
        return $e;
    }
    public function flush(): void {
        // cascade et contrôle des nouvelles entités découvertes via les relations
        $seen = new \SplObjectStorage();
        do {
            $added = false;
            foreach ($this->all() as $e) if (!$seen->contains($e)) { $seen->attach($e); $this->discover($e); $added = true; }
        } while ($added);
        $ops = [];
        // INSERT (parents d'abord)
        $pending = iterator_to_array((function () { foreach ($this->toInsert as $o) yield $o; })(), false);
        $guard = 0;
        while ($pending && $guard++ < 100) {
            foreach ($pending as $i => $e) {
                if (!$this->parentsReady($e, $pending)) continue;
                $this->callbacks($e, 'PrePersist');
                $ops[] = $this->insert($e);
                unset($pending[$i]);
            }
        }
        $this->toInsert = new \SplObjectStorage();
        // orphanRemoval : éléments retirés d'une collection
        foreach ($this->managed as $e) if (!in_array($e, $this->justInserted, true)) $this->orphans($e);
        // UPDATE
        foreach ($this->managed as $e) {
            if ($this->toDelete->contains($e) || in_array($e, $this->justInserted, true)) continue;
            $diff = $this->diff($e);
            if ($diff) {
                $this->callbacks($e, 'PreUpdate');
                $diff = $this->diff($e);
                $m = $this->meta($e::class);
                $set = implode(', ', array_map(fn($c, $v) => "$c = " . $this->fmt($v), array_keys($diff), $diff));
                $ops[] = 'UPDATE ' . $m['table'] . ' SET ' . $set . ' WHERE id = ' . $this->fmt($this->getVal($e, $m['id']));
            }
        }
        // DELETE
        foreach ($this->toDelete as $e) {
            $m = $this->meta($e::class);
            $id = $this->getVal($e, $m['id']);
            $ops[] = 'DELETE FROM ' . $m['table'] . ' WHERE id = ' . $this->fmt($id);
            $this->managed->detach($e);
            unset($this->identity[$e::class . '#' . $id], $this->db[$e::class . '#' . $id]);
        }
        $this->toDelete = new \SplObjectStorage();
        $this->justInserted = [];
        if (!$ops) return;
        $this->transactions++;
        $this->sql('START TRANSACTION');
        foreach ($ops as $q) $this->sql($q);
        $this->sql('COMMIT');
        foreach ($this->managed as $e) $this->managed[$e] = $this->snapshot($e);
    }

    // ---------- interne ----------
    private array $justInserted = [];
    private function sql(string $q): void { $this->log[] = $q; if ($this->echo) echo 'SQL> ', $q, "\n"; }
    private function all(): array {
        $out = [];
        foreach ($this->managed as $o) $out[] = $o;
        foreach ($this->toInsert as $o) $out[] = $o;
        return $out;
    }
    private function meta(string $class): array {
        if (isset($this->meta[$class])) return $this->meta[$class];
        $rc = new \ReflectionClass($class);
        if (!$rc->getAttributes('Doctrine\ORM\Mapping\Entity')) throw new ORMException("La classe $class n'est pas une entité : il manque #[ORM\\Entity].");
        $short = $rc->getShortName();
        $table = strtolower(preg_replace('/(?<!^)[A-Z]/', '_$0', $short));
        foreach ($rc->getAttributes('Doctrine\ORM\Mapping\Table') as $a) { $args = $a->getArguments(); if (isset($args['name'])) $table = $args['name']; }
        $m = ['table' => $table, 'id' => null, 'generated' => false, 'cols' => [], 'm2o' => [], 'o2m' => [], 'callbacks' => []];
        foreach ($rc->getProperties() as $p) {
            $names = array_map(fn($a) => $a->getName(), $p->getAttributes());
            $args = [];
            foreach ($p->getAttributes() as $a) $args[$a->getName()] = $a->getArguments();
            $col = strtolower(preg_replace('/(?<!^)[A-Z]/', '_$0', $p->getName()));
            if (in_array('Doctrine\ORM\Mapping\Id', $names, true)) { $m['id'] = $p->getName(); $m['generated'] = in_array('Doctrine\ORM\Mapping\GeneratedValue', $names, true); continue; }
            if (isset($args['Doctrine\ORM\Mapping\Column'])) { $m['cols'][$p->getName()] = $args['Doctrine\ORM\Mapping\Column']['name'] ?? $col; continue; }
            if (isset($args['Doctrine\ORM\Mapping\ManyToOne']) || isset($args['Doctrine\ORM\Mapping\OneToOne'])) {
                $a = $args['Doctrine\ORM\Mapping\ManyToOne'] ?? $args['Doctrine\ORM\Mapping\OneToOne'];
                $jc = $args['Doctrine\ORM\Mapping\JoinColumn'] ?? [];
                $m['m2o'][$p->getName()] = ['col' => $col . '_id', 'nullable' => $jc['nullable'] ?? true, 'cascade' => $a['cascade'] ?? []];
                continue;
            }
            if (isset($args['Doctrine\ORM\Mapping\OneToMany'])) {
                $a = $args['Doctrine\ORM\Mapping\OneToMany'];
                $m['o2m'][$p->getName()] = ['cascade' => $a['cascade'] ?? [], 'orphan' => $a['orphanRemoval'] ?? false, 'mappedBy' => $a['mappedBy'] ?? null];
            }
        }
        if (!$m['id']) throw new ORMException("L'entité $class n'a pas d'identifiant (#[ORM\\Id]).");
        if ($rc->getAttributes('Doctrine\ORM\Mapping\HasLifecycleCallbacks')) {
            foreach ($rc->getMethods() as $meth) foreach (['PrePersist', 'PreUpdate'] as $cb)
                if ($meth->getAttributes('Doctrine\ORM\Mapping\\' . $cb)) $m['callbacks'][$cb][] = $meth->getName();
        }
        $this->ids[$table] = $this->ids[$table] ?? 0;
        return $this->meta[$class] = $m;
    }
    private function getVal(object $e, string $prop): mixed {
        $p = new \ReflectionProperty($e, $prop);
        return $p->isInitialized($e) ? $p->getValue($e) : null;
    }
    private function setVal(object $e, string $prop, mixed $v): void { (new \ReflectionProperty($e, $prop))->setValue($e, $v); }
    private function row(object $e): array {
        $m = $this->meta($e::class);
        $row = [];
        foreach ($m['cols'] as $prop => $col) $row[$col] = $this->getVal($e, $prop);
        foreach ($m['m2o'] as $prop => $r) { $t = $this->getVal($e, $prop); $row[$r['col']] = $t ? $this->getVal($t, $this->meta($t::class)['id']) : null; }
        return $row;
    }
    private function snapshot(object $e): array {
        $s = ['row' => $this->norm($this->row($e)), 'coll' => []];
        foreach ($this->meta($e::class)['o2m'] as $prop => $r) { $c = $this->getVal($e, $prop); $s['coll'][$prop] = $c ? $c->toArray() : []; }
        return $s;
    }
    private function norm(array $row): array { return array_map(fn($v) => $this->fmt($v), $row); }
    private function diff(object $e): array {
        $old = $this->managed[$e]['row'];
        $new = $this->row($e);
        $out = [];
        foreach ($new as $c => $v) if (($old[$c] ?? null) !== $this->fmt($v)) $out[$c] = $v;
        return $out;
    }
    private function fmt(mixed $v): string {
        if ($v === null) return 'NULL';
        if (is_bool($v)) return $v ? '1' : '0';
        if (is_int($v) || is_float($v)) return (string) $v;
        if ($v instanceof \DateTimeInterface) return "'" . $v->format('Y-m-d H:i:s') . "'";
        if ($v instanceof \BackedEnum) return "'" . $v->value . "'";
        if ($v instanceof \UnitEnum) return "'" . $v->name . "'";
        if (is_object($v) && method_exists($v, '__toString')) return "'" . $v . "'";
        if (is_array($v)) return "'" . json_encode($v, JSON_UNESCAPED_UNICODE) . "'";
        return "'" . str_replace("'", "''", (string) $v) . "'";
    }
    private function insert(object $e): string {
        $m = $this->meta($e::class);
        foreach ($m['m2o'] as $prop => $r) {
            if (!$r['nullable'] && $this->getVal($e, $prop) === null)
                throw new ORMException('INSERT impossible dans ' . $m['table'] . ' : la colonne ' . $r['col'] . " ne peut pas être NULL. Le côté propriétaire (\$$prop) n'a pas été renseigné.");
        }
        $row = $this->row($e);
        if ($m['generated']) { $id = ++$this->ids[$m['table']]; $this->setVal($e, $m['id'], $id); }
        else { $id = $this->getVal($e, $m['id']); $row = [$m['id'] => $id] + $row; }
        $this->managed[$e] = $this->snapshot($e);
        $this->identity[$e::class . '#' . $id] = $e;
        $this->justInserted[] = $e;
        $cols = implode(', ', array_keys($row));
        $vals = implode(', ', array_map(fn($v) => $this->fmt($v), $row));
        return 'INSERT INTO ' . $m['table'] . ' (' . $cols . ') VALUES (' . $vals . ')';
    }
    private function parentsReady(object $e, array $pending): bool {
        foreach ($this->meta($e::class)['m2o'] as $prop => $r) { $t = $this->getVal($e, $prop); if ($t && $t !== $e && in_array($t, $pending, true)) return false; }
        return true;
    }
    private function cascade(object $e, string $op): void {
        $m = $this->meta($e::class);
        foreach ($m['o2m'] as $prop => $r) if (in_array($op, $r['cascade'], true)) {
            $c = $this->getVal($e, $prop);
            if ($c) foreach ($c as $child) $this->persist($child);
        }
        foreach ($m['m2o'] as $prop => $r) if (in_array($op, $r['cascade'], true)) { $t = $this->getVal($e, $prop); if ($t) $this->persist($t); }
    }
    private function discover(object $e): void {
        $m = $this->meta($e::class);
        foreach ($m['o2m'] as $prop => $r) {
            $c = $this->getVal($e, $prop); if (!$c) continue;
            foreach ($c as $child) {
                if ($this->managed->contains($child) || $this->toInsert->contains($child)) continue;
                if (in_array('persist', $r['cascade'], true)) { $this->persist($child); continue; }
            }
        }
        foreach ($m['m2o'] as $prop => $r) {
            $t = $this->getVal($e, $prop);
            if ($t && !$this->managed->contains($t) && !$this->toInsert->contains($t)) {
                if (in_array('persist', $r['cascade'], true)) { $this->persist($t); continue; }
                throw new ORMException('Une nouvelle entité ' . $t::class . " a été trouvée via la relation \$$prop de " . $e::class . ", mais elle n'a pas été persistée (persist() manquant ou cascade: ['persist'] absent).");
            }
        }
    }
    private function orphans(object $e): void {
        $m = $this->meta($e::class);
        foreach ($m['o2m'] as $prop => $r) {
            if (!$r['orphan']) continue;
            $before = $this->managed[$e]['coll'][$prop] ?? [];
            $c = $this->getVal($e, $prop); $now = $c ? $c->toArray() : [];
            foreach ($before as $old) if (!in_array($old, $now, true) && $this->managed->contains($old)) $this->toDelete->attach($old);
        }
    }
    private function callbacks(object $e, string $cb): void {
        foreach ($this->meta($e::class)['callbacks'][$cb] ?? [] as $meth) $e->$meth();
    }
}
PHPSIM);
"""
