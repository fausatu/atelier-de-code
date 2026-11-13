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
class HttpException extends \RuntimeException { public function __construct(public int $statusCode = 500, string $message = '', public array $headers = []) { parent::__construct($message); } public function getStatusCode(): int { return $this->statusCode; } public function getHeaders(): array { return $this->headers; } }
class BadRequestHttpException extends HttpException { public function __construct(string $message = 'Bad Request') { parent::__construct(400, $message); } }
class UnauthorizedHttpException extends HttpException { public function __construct(string $challenge = 'Bearer', string $message = 'Unauthorized') { parent::__construct(401, $message, ['WWW-Authenticate' => $challenge]); } }
class TooManyRequestsHttpException extends HttpException { public function __construct(int|string|null $retryAfter = null, string $message = 'Too Many Requests') { parent::__construct(429, $message, $retryAfter !== null ? ['Retry-After' => (string) $retryAfter] : []); } }
class PreconditionFailedHttpException extends HttpException { public function __construct(string $message = 'Precondition Failed') { parent::__construct(412, $message); } }
class NotFoundHttpException extends HttpException { public function __construct(string $message = 'Not Found') { parent::__construct(404, $message); } }
class AccessDeniedHttpException extends HttpException { public function __construct(string $message = 'Access Denied') { parent::__construct(403, $message); } }
class ConflictHttpException extends HttpException { public function __construct(string $message = 'Conflict') { parent::__construct(409, $message); } }
class UnprocessableEntityHttpException extends HttpException { public function __construct(string $message = 'Unprocessable Entity') { parent::__construct(422, $message); } }

namespace Symfony\Component\HttpFoundation;
class HeaderBag {
    private array $h = [];
    public function __construct(array $headers = []) { foreach ($headers as $k => $v) $this->set($k, $v); }
    public function get(string $k, ?string $default = null): ?string { return $this->h[strtolower($k)][1] ?? $default; }
    public function set(string $k, string|int|null $v): void { if ($v === null) { $this->remove($k); return; } $this->h[strtolower($k)] = [$k, (string) $v]; }
    public function has(string $k): bool { return isset($this->h[strtolower($k)]); }
    public function remove(string $k): void { unset($this->h[strtolower($k)]); }
    public function all(): array { $o = []; foreach ($this->h as [$k, $v]) $o[$k] = $v; return $o; }
}
class ParameterBag {
    public function __construct(private array $p = []) {}
    public function get(string $k, mixed $default = null): mixed { return $this->p[$k] ?? $default; }
    public function getInt(string $k, int $default = 0): int { return isset($this->p[$k]) ? (int) $this->p[$k] : $default; }
    public function has(string $k): bool { return array_key_exists($k, $this->p); }
    public function all(): array { return $this->p; }
    public function set(string $k, mixed $v): void { $this->p[$k] = $v; }
    public function remove(string $k): void { unset($this->p[$k]); }
}
class Request {
    public HeaderBag $headers; public ParameterBag $query; public ParameterBag $attributes;
    public function __construct(private string $method = 'GET', private string $path = '/', array $query = [], private ?array $body = null, array $headers = []) {
        $this->headers = new HeaderBag($headers); $this->query = new ParameterBag($query); $this->attributes = new ParameterBag([]);
    }
    public function getMethod(): string { return $this->method; }
    public function getPathInfo(): string { return $this->path; }
    public function toArray(): array { return $this->body ?? []; }
    public function getContent(): string { return $this->body === null ? '' : json_encode($this->body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); }
    public function getClientIp(): string { return $this->headers->get('X-Client-Ip', '127.0.0.1'); }
}
class JsonResponse {
    public HeaderBag $headers;
    public function __construct(public mixed $data = null, public int $status = 200, array $headers = []) { $this->headers = new HeaderBag($headers); }
    public function getStatusCode(): int { return $this->status; }
    public function setStatusCode(int $s): static { $this->status = $s; return $this; }
}
class Response extends JsonResponse {
    public const HTTP_OK = 200; public const HTTP_CREATED = 201; public const HTTP_NO_CONTENT = 204; public const HTTP_NOT_MODIFIED = 304;
    public const HTTP_BAD_REQUEST = 400; public const HTTP_UNAUTHORIZED = 401; public const HTTP_FORBIDDEN = 403; public const HTTP_NOT_FOUND = 404;
    public const HTTP_CONFLICT = 409; public const HTTP_PRECONDITION_FAILED = 412; public const HTTP_UNPROCESSABLE_ENTITY = 422; public const HTTP_TOO_MANY_REQUESTS = 429;
}

namespace Symfony\Bundle\FrameworkBundle\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
abstract class AbstractController {
    protected function json(mixed $data, int $status = 200, array $headers = []): JsonResponse { return new JsonResponse($data, $status, $headers); }
    protected function createNotFoundException(string $message = 'Not Found'): NotFoundHttpException { return new NotFoundHttpException($message); }
}

namespace Symfony\Component\EventDispatcher\Attribute;
#[\Attribute(\Attribute::TARGET_CLASS | \Attribute::TARGET_METHOD | \Attribute::IS_REPEATABLE)]
class AsEventListener { public function __construct(public ?string $event = null, public ?string $method = null, public int $priority = 0) {} }

namespace Symfony\Component\HttpKernel;
final class KernelEvents { const EXCEPTION = 'kernel.exception'; const REQUEST = 'kernel.request'; const RESPONSE = 'kernel.response'; }

namespace Symfony\Component\HttpKernel\Event;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
final class RequestEvent {
    private ?JsonResponse $response = null;
    public function __construct(private Request $request) {}
    public function getRequest(): Request { return $this->request; }
    public function setResponse(JsonResponse $r): void { $this->response = $r; }
    public function getResponse(): ?JsonResponse { return $this->response; }
    public function hasResponse(): bool { return $this->response !== null; }
    public function isMainRequest(): bool { return true; }
}
final class ResponseEvent {
    public function __construct(private Request $request, private JsonResponse $response) {}
    public function getRequest(): Request { return $this->request; }
    public function getResponse(): JsonResponse { return $this->response; }
    public function setResponse(JsonResponse $r): void { $this->response = $r; }
}
final class ExceptionEvent {
    private ?JsonResponse $response = null;
    public function __construct(private \Throwable $throwable) {}
    public function getThrowable(): \Throwable { return $this->throwable; }
    public function getRequest(): \Symfony\Component\HttpFoundation\Request { return \Atelier\App::$current ?? new \Symfony\Component\HttpFoundation\Request(); }
    public function setResponse(JsonResponse $r): void { $this->response = $r; }
    public function getResponse(): ?JsonResponse { return $this->response; }
    public function hasResponse(): bool { return $this->response !== null; }
}

namespace Symfony\Component\Serializer\Exception;
class CircularReferenceException extends \RuntimeException {}

namespace Atelier;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Symfony\Component\Validator\Validator;

final class HttpResult {
    public function __construct(public int $status, public mixed $json, public array $headers = []) {}
    public function json(): mixed { return $this->json; }
    public function header(string $name): ?string { foreach ($this->headers as $k => $v) if (strcasecmp($k, $name) === 0) return $v; return null; }
    public function __toString(): string {
        $h = ''; foreach ($this->headers as $k => $v) $h .= " [$k: $v]";
        return $this->status . $h . ($this->json === null ? '' : ' ' . json_encode($this->json, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    }
}

final class App {
    public static array $services = [];
    /** classe d'entité => fn(int $id): ?object  (pour les paramètres de route typés entité) */
    public static array $entities = [];
    public static ?object $user = null;
    public static bool $echo = true;
    private static array $instances = [];

    public static function reset(): void { self::$services = []; self::$entities = []; self::$user = null; self::$instances = []; self::$building = []; }
    public static function set(string $type, object $service): void { self::$services[$type] = $service; }

    private static array $building = [];
    public static function get(string $type): object {
        if (isset(self::$services[$type])) return self::$services[$type];
        if (isset(self::$instances[$type])) return self::$instances[$type];
        if (in_array($type, self::$building, true)) { $chain = implode(' -> ', array_merge(self::$building, [$type])); self::$building = []; throw new \LogicException("Dépendance circulaire : $chain"); }
        self::$building[] = $type;
        try { return self::build($type); } finally { array_pop(self::$building); }
    }
    private static function build(string $type): object {
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

    public static ?\Symfony\Component\HttpFoundation\Request $current = null;
    public static function request(string $method, string $uri, ?array $body = null, array $headers = []): HttpResult {
        $parts = parse_url($uri);
        $path = rtrim($parts['path'] ?? '/', '/') ?: '/';
        parse_str($parts['query'] ?? '', $query);
        $req = self::$current = new \Symfony\Component\HttpFoundation\Request($method, $path, $query, $body, $headers);
        try {
            [$class, $action, $params] = self::route($method, $path);
            $req->attributes = new \Symfony\Component\HttpFoundation\ParameterBag($params + ['_route' => "$class::$action"]);
            $res = null;
            $ev = new \Symfony\Component\HttpKernel\Event\RequestEvent($req);
            foreach (self::listeners('kernel.request') as [$c, $meth]) { self::get($c)->$meth($ev); if ($ev->hasResponse()) { $res = self::result($ev->getResponse()); break; } }
            $res ??= self::call($class, $action, $params, $body, $query);
        } catch (\Throwable $e) {
            $res = self::error($e);
        }
        if (self::$echo) echo 'HTTP> ', $method, ' ', $uri, ($headers ? ' ' . json_encode($headers, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : ''), ($body !== null ? ' ' . json_encode($body, JSON_UNESCAPED_UNICODE) : ''), "\n     ", $res, "\n";
        return $res;
    }
    /** @return list<array{0: string, 1: string}> classe + méthode des listeners d'un évènement, par priorité décroissante */
    private static function listeners(string $event): array {
        $out = [];
        foreach (get_declared_classes() as $c) {
            $rc = new \ReflectionClass($c);
            foreach ($rc->getAttributes(\Symfony\Component\EventDispatcher\Attribute\AsEventListener::class) as $a) { $l = $a->newInstance(); if ($l->event === $event) $out[] = [$c, $l->method ?? '__invoke', $l->priority]; }
            foreach ($rc->getMethods() as $m) foreach ($m->getAttributes(\Symfony\Component\EventDispatcher\Attribute\AsEventListener::class) as $a) { $l = $a->newInstance(); if ($l->event === $event) $out[] = [$c, $m->getName(), $l->priority]; }
        }
        usort($out, fn($x, $y) => $y[2] <=> $x[2]);
        return $out;
    }
    private static function result(JsonResponse $r): HttpResult {
        if (self::$current) {
            $ev = new \Symfony\Component\HttpKernel\Event\ResponseEvent(self::$current, $r);
            foreach (self::listeners('kernel.response') as [$c, $meth]) self::get($c)->$meth($ev);
            $r = $ev->getResponse();
        }
        return new HttpResult($r->status, $r->status === 204 || $r->status === 304 ? null : self::normalize($r->data), $r->headers->all());
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
            if ($tn === \Symfony\Component\HttpFoundation\Request::class) { $args[] = self::$current; continue; }
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
        return self::result($res);
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
        $event = new \Symfony\Component\HttpKernel\Event\ExceptionEvent($e);
        foreach (get_declared_classes() as $c) {
            $rc = new \ReflectionClass($c);
            $targets = [];
            foreach ($rc->getAttributes(\Symfony\Component\EventDispatcher\Attribute\AsEventListener::class) as $a) { $l = $a->newInstance(); if ($l->event === 'kernel.exception') $targets[] = $l->method ?? '__invoke'; }
            foreach ($rc->getMethods() as $m) foreach ($m->getAttributes(\Symfony\Component\EventDispatcher\Attribute\AsEventListener::class) as $a) { $l = $a->newInstance(); if ($l->event === 'kernel.exception') $targets[] = $m->getName(); }
            foreach ($targets as $meth) {
                self::get($c)->$meth($event);
                if ($event->hasResponse()) return self::result($event->getResponse());
            }
        }
        if ($e instanceof HttpException) return new HttpResult($e->statusCode, ['error' => $e->getMessage()], $e->headers);
        foreach ((new \ReflectionClass($e))->getAttributes(\Symfony\Component\HttpKernel\Attribute\WithHttpStatus::class) as $a)
            return new HttpResult($a->newInstance()->statusCode, ['error' => $e->getMessage()]);
        $p = get_parent_class($e);
        while ($p) { foreach ((new \ReflectionClass($p))->getAttributes(\Symfony\Component\HttpKernel\Attribute\WithHttpStatus::class) as $a) return new HttpResult($a->newInstance()->statusCode, ['error' => $e->getMessage()]); $p = get_parent_class($p); }
        return new HttpResult(500, ['error' => get_class($e) . ' : ' . $e->getMessage()]);
    }
}
PHPSF);
"""
