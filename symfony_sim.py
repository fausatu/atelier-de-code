"""Mini-Symfony simulé en PHP pur (RUN setup), pour les parcours DTO et Architecture.

- Contraintes de validation (#[Assert\\NotBlank], Length, Email, Range…) et un validateur.
- Attributs Route, MapRequestPayload, MapQueryString, CurrentUser, WithHttpStatus.
- AbstractController::json(), exceptions HTTP, JsonResponse.
- App::request('POST', '/api/...', [...json...]) : trouve la route, construit le contrôleur
  (autowiring), remplit et valide les DTO, appelle l'action, convertit les exceptions
  en statut HTTP, sérialise la réponse (avec détection de référence circulaire).
"""

SYMFONY_SETUP = r"""
eval(<<<'PHPSF'
namespace Symfony\Component\Validator\Constraints;

abstract class Constraint { public ?string $message = null; public function msg(string $default, array $p = []): string { $m = $this->message ?? $default; foreach ($p as $k => $v) $m = str_replace('{{ ' . $k . ' }}', (string) $v, $m); return $m; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class NotBlank extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class NotNull extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Length extends Constraint { public function __construct(public ?int $min = null, public ?int $max = null, ?string $message = null, public ?int $exactly = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Email extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Positive extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class PositiveOrZero extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Range extends Constraint { public function __construct(public int|float|null $min = null, public int|float|null $max = null, ?string $message = null, ?string $notInRangeMessage = null) { $this->message = $message ?? $notInRangeMessage; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Regex extends Constraint { public function __construct(public string $pattern = '', ?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class IsTrue extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Count extends Constraint { public function __construct(public ?int $min = null, public ?int $max = null, ?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class All extends Constraint { public function __construct(public array $constraints = []) {} }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Date extends Constraint { public function __construct(?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Choice extends Constraint { public function __construct(public array $choices = [], ?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class GreaterThan extends Constraint { public function __construct(public mixed $value = null, ?string $message = null) { $this->message = $message; } }
#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_PARAMETER | \Attribute::IS_REPEATABLE)]
class Valid extends Constraint { public function __construct() {} }

namespace Symfony\Component\Validator;

use Symfony\Component\Validator\Constraints as A;

final class Validator {
    /** @return list<array{propertyPath: string, title: string}> */
    public static function validate(object $o, string $prefix = ''): array {
        $out = [];
        foreach ((new \ReflectionClass($o))->getProperties() as $p) {
            $v = $p->isInitialized($o) ? $p->getValue($o) : null;
            $path = $prefix . $p->getName();
            foreach ($p->getAttributes() as $attr) {
                if (!is_subclass_of($attr->getName(), A\Constraint::class)) continue;
                $c = $attr->newInstance();
                if ($c instanceof A\Valid) {
                    if (is_object($v)) $out = array_merge($out, self::validate($v, $path . '.'));
                    if (is_array($v)) foreach ($v as $i => $item) if (is_object($item)) $out = array_merge($out, self::validate($item, $path . '[' . $i . '].'));
                    continue;
                }
                foreach (self::check($c, $v) as $msg) $out[] = ['propertyPath' => $path, 'title' => $msg];
            }
        }
        return $out;
    }
    public static function check(A\Constraint $c, mixed $v): array {
        $e = [];
        $len = fn($s) => (int) preg_match_all('/./us', (string) $s);
        switch (true) {
            case $c instanceof A\NotBlank: if ($v === null || $v === '' || $v === [] || $v === false) $e[] = $c->msg('Cette valeur ne doit pas être vide.'); break;
            case $c instanceof A\NotNull: if ($v === null) $e[] = $c->msg('Cette valeur ne doit pas être nulle.'); break;
            case $c instanceof A\IsTrue: if ($v !== true) $e[] = $c->msg('Cette valeur doit être vraie.'); break;
            case $v === null: break;
            case $c instanceof A\Length:
                $l = $len($v);
                if ($c->exactly !== null && $l !== $c->exactly) $e[] = $c->msg('Cette valeur doit contenir exactement {{ limit }} caractères.', ['limit' => $c->exactly]);
                elseif ($c->min !== null && $l < $c->min) $e[] = $c->msg('Cette chaîne est trop courte. Elle doit avoir au minimum {{ limit }} caractères.', ['limit' => $c->min]);
                elseif ($c->max !== null && $l > $c->max) $e[] = $c->msg('Cette chaîne est trop longue. Elle doit avoir au maximum {{ limit }} caractères.', ['limit' => $c->max]);
                break;
            case $c instanceof A\Email: if ($v !== '' && !filter_var($v, FILTER_VALIDATE_EMAIL)) $e[] = $c->msg("Cette valeur n'est pas une adresse email valide."); break;
            case $c instanceof A\Positive: if (!(is_numeric($v) && $v > 0)) $e[] = $c->msg('Cette valeur doit être strictement positive.'); break;
            case $c instanceof A\PositiveOrZero: if (!(is_numeric($v) && $v >= 0)) $e[] = $c->msg('Cette valeur doit être supérieure ou égale à zéro.'); break;
            case $c instanceof A\Range:
                if (($c->min !== null && $v < $c->min) || ($c->max !== null && $v > $c->max)) $e[] = $c->msg('Cette valeur doit être comprise entre {{ min }} et {{ max }}.', ['min' => $c->min, 'max' => $c->max]);
                break;
            case $c instanceof A\Regex: if ($v !== '' && !preg_match($c->pattern, (string) $v)) $e[] = $c->msg("Cette valeur n'est pas valide."); break;
            case $c instanceof A\Count:
                $n = is_countable($v) ? count($v) : 0;
                if ($c->min !== null && $n < $c->min) $e[] = $c->msg('Cette collection doit contenir {{ limit }} éléments ou plus.', ['limit' => $c->min]);
                if ($c->max !== null && $n > $c->max) $e[] = $c->msg('Cette collection doit contenir {{ limit }} éléments ou moins.', ['limit' => $c->max]);
                break;
            case $c instanceof A\All: if (is_iterable($v)) foreach ($v as $item) foreach ($c->constraints as $sub) $e = array_merge($e, self::check($sub, $item)); break;
            case $c instanceof A\Date:
                if ($v !== '') { $d = \DateTimeImmutable::createFromFormat('!Y-m-d', (string) $v); if (!$d || $d->format('Y-m-d') !== $v) $e[] = $c->msg("Cette valeur n'est pas une date valide."); }
                break;
            case $c instanceof A\Choice: if ($v !== '' && !in_array($v, $c->choices, true)) $e[] = $c->msg("Cette valeur doit être l'un des choix proposés."); break;
            case $c instanceof A\GreaterThan:
                $cmp = $c->value;
                if (is_string($cmp) && $v instanceof \DateTimeInterface) $cmp = new \DateTimeImmutable($cmp);
                if (!($v > $cmp)) $e[] = $c->msg('Cette valeur doit être supérieure à {{ compared_value }}.', ['compared_value' => is_object($c->value) ? '' : $c->value]);
                break;
        }
        return $e;
    }
}

namespace Symfony\Component\Routing\Attribute;
#[\Attribute(\Attribute::TARGET_METHOD | \Attribute::TARGET_CLASS)]
class Route { public function __construct(public string $path = '', public array $methods = [], public ?string $name = null) {} }

namespace Symfony\Component\HttpKernel\Attribute;
#[\Attribute(\Attribute::TARGET_PARAMETER)] class MapRequestPayload { public function __construct() {} }
#[\Attribute(\Attribute::TARGET_PARAMETER)] class MapQueryString { public function __construct() {} }
#[\Attribute(\Attribute::TARGET_CLASS)] class WithHttpStatus { public function __construct(public int $statusCode = 500) {} }

namespace Symfony\Component\Security\Http\Attribute;
#[\Attribute(\Attribute::TARGET_PARAMETER)] class CurrentUser { public function __construct() {} }

namespace Symfony\Component\HttpKernel\Exception;
class HttpException extends \RuntimeException { public function __construct(public int $statusCode = 500, string $message = '') { parent::__construct($message); } }
class NotFoundHttpException extends HttpException { public function __construct(string $message = 'Not Found') { parent::__construct(404, $message); } }
class AccessDeniedHttpException extends HttpException { public function __construct(string $message = 'Access Denied') { parent::__construct(403, $message); } }
class ConflictHttpException extends HttpException { public function __construct(string $message = 'Conflict') { parent::__construct(409, $message); } }
class UnprocessableEntityHttpException extends HttpException { public function __construct(string $message = 'Unprocessable Entity') { parent::__construct(422, $message); } }

namespace Symfony\Component\HttpFoundation;
class JsonResponse { public function __construct(public mixed $data = null, public int $status = 200) {} public function getStatusCode(): int { return $this->status; } }
class Response extends JsonResponse {}

namespace Symfony\Bundle\FrameworkBundle\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
abstract class AbstractController {
    protected function json(mixed $data, int $status = 200): JsonResponse { return new JsonResponse($data, $status); }
    protected function createNotFoundException(string $message = 'Not Found'): NotFoundHttpException { return new NotFoundHttpException($message); }
}

namespace Symfony\Component\Serializer\Exception;
class CircularReferenceException extends \RuntimeException {}

namespace Atelier;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Symfony\Component\Validator\Validator;

final class HttpResult {
    public function __construct(public int $status, public mixed $json) {}
    public function json(): mixed { return $this->json; }
    public function __toString(): string { return $this->status . ' ' . json_encode($this->json, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); }
}

final class App {
    public static array $services = [];
    /** classe d'entité => fn(int $id): ?object  (pour les paramètres de route typés entité) */
    public static array $entities = [];
    public static ?object $user = null;
    public static bool $echo = true;
    private static array $instances = [];

    public static function reset(): void { self::$services = []; self::$entities = []; self::$user = null; self::$instances = []; }
    public static function set(string $type, object $service): void { self::$services[$type] = $service; }

    public static function get(string $type): object {
        if (isset(self::$services[$type])) return self::$services[$type];
        if (isset(self::$instances[$type])) return self::$instances[$type];
        foreach (self::$services as $s) if ($s instanceof $type) return $s;
        if (!class_exists($type)) throw new \LogicException("Autowiring : aucun service pour $type (interface sans implémentation enregistrée ?).");
        $rc = new \ReflectionClass($type);
        if (!$rc->isInstantiable()) throw new \LogicException("Autowiring : $type n'est pas instanciable.");
        $args = [];
        foreach ($rc->getConstructor()?->getParameters() ?? [] as $p) {
            $t = $p->getType();
            if ($t instanceof \ReflectionNamedType && !$t->isBuiltin()) $args[] = self::get($t->getName());
            elseif ($p->isDefaultValueAvailable()) $args[] = $p->getDefaultValue();
            else throw new \LogicException("Autowiring : impossible de fournir \$" . $p->getName() . " à $type.");
        }
        return self::$instances[$type] = $rc->newInstanceArgs($args);
    }

    public static function request(string $method, string $uri, ?array $body = null): HttpResult {
        $parts = parse_url($uri);
        $path = rtrim($parts['path'] ?? '/', '/') ?: '/';
        parse_str($parts['query'] ?? '', $query);
        try {
            [$class, $action, $params] = self::route($method, $path);
            $res = self::call($class, $action, $params, $body, $query);
        } catch (\Throwable $e) {
            $res = self::error($e);
        }
        if (self::$echo) echo 'HTTP> ', $method, ' ', $uri, ($body !== null ? ' ' . json_encode($body, JSON_UNESCAPED_UNICODE) : ''), "\n     ", $res, "\n";
        return $res;
    }

    private static function route(string $method, string $path): array {
        $allowed = false;
        foreach (get_declared_classes() as $c) {
            if (!is_subclass_of($c, \Symfony\Bundle\FrameworkBundle\Controller\AbstractController::class)) continue;
            $prefix = '';
            foreach ((new \ReflectionClass($c))->getAttributes(\Symfony\Component\Routing\Attribute\Route::class) as $a) $prefix = $a->newInstance()->path;
            foreach ((new \ReflectionClass($c))->getMethods() as $m) foreach ($m->getAttributes(\Symfony\Component\Routing\Attribute\Route::class) as $a) {
                $r = $a->newInstance();
                $pat = rtrim($prefix . $r->path, '/') ?: '/';
                $rx = '#^' . preg_replace('#\{(\w+)\}#', '(?P<$1>[^/]+)', $pat) . '$#';
                if (!preg_match($rx, $path, $mm)) continue;
                if ($r->methods && !in_array($method, $r->methods, true)) { $allowed = true; continue; }
                return [$c, $m->getName(), array_filter($mm, 'is_string', ARRAY_FILTER_USE_KEY)];
            }
        }
        throw new HttpException($allowed ? 405 : 404, $allowed ? 'Méthode non autorisée' : "Aucune route pour $method $path");
    }

    private static function call(string $class, string $action, array $params, ?array $body, array $query): HttpResult {
        $ctrl = self::get($class);
        $args = [];
        foreach ((new \ReflectionMethod($class, $action))->getParameters() as $p) {
            $t = $p->getType(); $tn = $t instanceof \ReflectionNamedType ? $t->getName() : null;
            if ($p->getAttributes(\Symfony\Component\HttpKernel\Attribute\MapRequestPayload::class)) {
                $dto = self::denormalize($tn, $body ?? []);
                $v = Validator::validate($dto);
                if ($v) return new HttpResult(422, ['title' => 'Validation Failed', 'violations' => $v]);
                $args[] = $dto; continue;
            }
            if ($p->getAttributes(\Symfony\Component\HttpKernel\Attribute\MapQueryString::class)) {
                if (!$query) { $args[] = $p->allowsNull() ? null : self::denormalize($tn, []); continue; }
                $dto = self::denormalize($tn, $query, true);
                $v = Validator::validate($dto);
                if ($v) return new HttpResult(422, ['title' => 'Validation Failed', 'violations' => $v]);
                $args[] = $dto; continue;
            }
            if ($p->getAttributes(\Symfony\Component\Security\Http\Attribute\CurrentUser::class)) {
                if (!self::$user && !$p->allowsNull()) return new HttpResult(401, ['error' => 'Non connecté']);
                $args[] = self::$user; continue;
            }
            if (array_key_exists($p->getName(), $params)) {
                $raw = $params[$p->getName()];
                $args[] = $tn === 'int' ? (int) $raw : $raw; continue;
            }
            if ($tn && isset(self::$entities[$tn]) && isset($params['id'])) {
                $e = (self::$entities[$tn])((int) $params['id']);
                if (!$e) return new HttpResult(404, ['error' => "$tn introuvable"]);
                $args[] = $e; continue;
            }
            if ($tn && !$t->isBuiltin()) { $args[] = self::get($tn); continue; }
            if ($p->isDefaultValueAvailable()) { $args[] = $p->getDefaultValue(); continue; }
            throw new \LogicException("Impossible de fournir l'argument \$" . $p->getName() . " de $class::$action().");
        }
        $res = $ctrl->$action(...$args);
        if (!$res instanceof JsonResponse) throw new \LogicException("$class::$action() doit renvoyer une réponse (\$this->json(...)).");
        return new HttpResult($res->status, self::normalize($res->data));
    }

    public static function denormalize(string $class, array $data, bool $fromQuery = false): object {
        $rc = new \ReflectionClass($class);
        $args = [];
        foreach ($rc->getConstructor()?->getParameters() ?? [] as $p) {
            $name = $p->getName();
            $t = $p->getType(); $tn = $t instanceof \ReflectionNamedType ? $t->getName() : 'mixed';
            if (!array_key_exists($name, $data)) {
                if ($p->isDefaultValueAvailable()) { $args[$name] = $p->getDefaultValue(); continue; }
                if ($t && $t->allowsNull()) { $args[$name] = null; continue; }
                throw new HttpException(422, "Le champ \"$name\" est obligatoire.");
            }
            $v = $data[$name];
            if ($v === null && $t && !$t->allowsNull()) throw new HttpException(422, "Le champ \"$name\" ne peut pas être null.");
            if ($v !== null && $fromQuery) {
                if ($tn === 'int' && is_numeric($v)) $v = (int) $v;
                elseif ($tn === 'float' && is_numeric($v)) $v = (float) $v;
                elseif ($tn === 'bool') $v = in_array($v, ['1', 'true', true, 1], true) ? true : (in_array($v, ['0', 'false', false, 0], true) ? false : $v);
            }
            if ($v !== null && $t instanceof \ReflectionNamedType && !$t->isBuiltin() && is_array($v) && class_exists($tn)) $v = self::denormalize($tn, $v, $fromQuery);
            $ok = match ($tn) { 'int' => is_int($v), 'float' => is_float($v) || is_int($v), 'string' => is_string($v), 'bool' => is_bool($v), 'array' => is_array($v), default => true };
            if ($v !== null && !$ok) throw new HttpException(422, "Le champ \"$name\" doit être de type $tn.");
            $args[$name] = $tn === 'float' && is_int($v) ? (float) $v : $v;
        }
        return $rc->newInstanceArgs($args);
    }

    public static function normalize(mixed $v, array $stack = []): mixed {
        if ($v === null || is_scalar($v)) return $v;
        if ($v instanceof \DateTimeInterface) return $v->format(DATE_ATOM);
        if ($v instanceof \BackedEnum) return $v->value;
        if (is_iterable($v)) { $o = []; foreach ($v as $k => $x) $o[$k] = self::normalize($x, $stack); return $o; }
        if (is_object($v)) {
            if (in_array($v, $stack, true)) throw new \Symfony\Component\Serializer\Exception\CircularReferenceException('Référence circulaire détectée en sérialisant ' . $v::class . ' (une entité renvoie vers une autre qui renvoie vers elle).');
            $stack[] = $v;
            $o = [];
            foreach ((new \ReflectionClass($v))->getProperties(\ReflectionProperty::IS_PUBLIC) as $p) if (!$p->isStatic() && $p->isInitialized($v)) $o[$p->getName()] = self::normalize($p->getValue($v), $stack);
            foreach ((new \ReflectionClass($v))->getMethods(\ReflectionMethod::IS_PUBLIC) as $m) {
                if ($m->isStatic() || $m->getNumberOfRequiredParameters() > 0) continue;
                if (preg_match('/^(get|is|has)([A-Z]\w*)$/', $m->getName(), $mm)) { $k = lcfirst($mm[2]); if (!array_key_exists($k, $o)) $o[$k] = self::normalize($m->invoke($v), $stack); }
            }
            return $o;
        }
        return null;
    }

    private static function error(\Throwable $e): HttpResult {
        if ($e instanceof HttpException) return new HttpResult($e->statusCode, ['error' => $e->getMessage()]);
        foreach ((new \ReflectionClass($e))->getAttributes(\Symfony\Component\HttpKernel\Attribute\WithHttpStatus::class) as $a)
            return new HttpResult($a->newInstance()->statusCode, ['error' => $e->getMessage()]);
        $p = get_parent_class($e);
        while ($p) { foreach ((new \ReflectionClass($p))->getAttributes(\Symfony\Component\HttpKernel\Attribute\WithHttpStatus::class) as $a) return new HttpResult($a->newInstance()->statusCode, ['error' => $e->getMessage()]); $p = get_parent_class($p); }
        return new HttpResult(500, ['error' => get_class($e) . ' : ' . $e->getMessage()]);
    }
}
PHPSF);
"""
