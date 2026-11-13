"""HttpClient Symfony simulé (MockHttpClient / MockResponse) + cache ArrayAdapter, pour le parcours API.

Même API que Symfony : $client->request('GET', $url, ['query' => …, 'headers' => …, 'json' => …, 'timeout' => …]),
$response->getStatusCode(), ->getHeaders(), ->getContent(), ->toArray() (qui lève ClientException / ServerException
sur 4xx / 5xx, sauf avec false). MockResponse peut simuler une coupure réseau ('error' => '…').
Le client affiche chaque appel (CLIENT> GET … → 200) et garde la liste dans $client->appels.
"""

HTTPCLIENT_SETUP = r"""
eval(<<<'PHPHC'
namespace Symfony\Contracts\HttpClient\Exception;
interface ExceptionInterface extends \Throwable {}
interface TransportExceptionInterface extends ExceptionInterface {}
interface HttpExceptionInterface extends ExceptionInterface { public function getResponse(): \Symfony\Contracts\HttpClient\ResponseInterface; }
interface ClientExceptionInterface extends HttpExceptionInterface {}
interface ServerExceptionInterface extends HttpExceptionInterface {}
interface RedirectionExceptionInterface extends HttpExceptionInterface {}
interface DecodingExceptionInterface extends ExceptionInterface {}

namespace Symfony\Contracts\HttpClient;
interface ResponseInterface {
    public function getStatusCode(): int;
    public function getHeaders(bool $throw = true): array;
    public function getContent(bool $throw = true): string;
    public function toArray(bool $throw = true): array;
}
interface HttpClientInterface { public function request(string $method, string $url, array $options = []): ResponseInterface; }

namespace Symfony\Component\HttpClient\Exception;
use Symfony\Contracts\HttpClient\ResponseInterface;
abstract class HttpExceptionBase extends \RuntimeException {
    public function __construct(private ResponseInterface $response) {
        parent::__construct(sprintf('HTTP %d returned for "%s".', $response->getStatusCode(), $response->url ?? ''), $response->getStatusCode());
    }
    public function getResponse(): ResponseInterface { return $this->response; }
}
final class ClientException extends HttpExceptionBase implements \Symfony\Contracts\HttpClient\Exception\ClientExceptionInterface {}
final class ServerException extends HttpExceptionBase implements \Symfony\Contracts\HttpClient\Exception\ServerExceptionInterface {}
final class RedirectionException extends HttpExceptionBase implements \Symfony\Contracts\HttpClient\Exception\RedirectionExceptionInterface {}
final class TransportException extends \RuntimeException implements \Symfony\Contracts\HttpClient\Exception\TransportExceptionInterface {}
final class JsonException extends \RuntimeException implements \Symfony\Contracts\HttpClient\Exception\DecodingExceptionInterface {}

namespace Symfony\Component\HttpClient\Response;
use Symfony\Contracts\HttpClient\ResponseInterface;
use Symfony\Component\HttpClient\Exception\{ClientException, ServerException, RedirectionException, TransportException, JsonException};
class MockResponse implements ResponseInterface {
    public ?string $url = null; public ?string $method = null; public array $options = [];
    /** $info : ['http_code' => 200, 'response_headers' => ['Content-Type' => '…'], 'error' => 'message de coupure réseau'] */
    public function __construct(private string $body = '', private array $info = []) {}
    public static function json(mixed $data, int $status = 200, array $headers = []): self { return new self(json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), ['http_code' => $status, 'response_headers' => $headers + ['Content-Type' => 'application/json']]); }
    public function getRequestMethod(): ?string { return $this->method; }
    public function getRequestUrl(): ?string { return $this->url; }
    public function getRequestOptions(): array { return $this->options; }
    private function transport(): void { if (!empty($this->info['error'])) throw new TransportException($this->info['error'] . ' for "' . $this->url . '".'); }
    public function getStatusCode(): int { $this->transport(); return (int) ($this->info['http_code'] ?? 200); }
    public function getHeaders(bool $throw = true): array {
        $this->check($throw); $o = [];
        foreach ($this->info['response_headers'] ?? [] as $k => $v) $o[strtolower($k)] = [(string) $v];
        return $o;
    }
    public function getContent(bool $throw = true): string { $this->check($throw); return $this->body; }
    public function toArray(bool $throw = true): array {
        $c = $this->getContent($throw);
        if ($c === '') throw new JsonException('Response body is empty.');
        $d = json_decode($c, true);
        if (!is_array($d)) throw new JsonException('JSON content was expected to decode to an array, ' . gettype($d) . ' returned for "' . $this->url . '".');
        return $d;
    }
    private function check(bool $throw): void {
        $s = $this->getStatusCode();
        if (!$throw) return;
        if ($s >= 500) throw new ServerException($this);
        if ($s >= 400) throw new ClientException($this);
        if ($s >= 300) throw new RedirectionException($this);
    }
}

namespace Symfony\Component\HttpClient;
use Symfony\Contracts\HttpClient\{HttpClientInterface, ResponseInterface};
use Symfony\Component\HttpClient\Response\MockResponse;
final class MockHttpClient implements HttpClientInterface {
    public static bool $echo = true;
    /** @var list<array{method: string, url: string, options: array}> */
    public array $appels = [];
    /** @param callable|MockResponse|list<MockResponse> $factory  callable(string $method, string $url, array $options): MockResponse */
    public function __construct(private mixed $factory = null, private ?string $baseUri = null) {}
    public function getRequestsCount(): int { return count($this->appels); }
    public function withOptions(array $o): static { $c = clone $this; if (isset($o['base_uri'])) $c->baseUri = $o['base_uri']; return $c; }
    public function request(string $method, string $url, array $options = []): ResponseInterface {
        $base = $options['base_uri'] ?? $this->baseUri;
        if ($base && !preg_match('#^https?://#', $url)) $url = rtrim($base, '/') . '/' . ltrim($url, '/');
        if (!empty($options['query'])) $url .= (str_contains($url, '?') ? '&' : '?') . http_build_query($options['query']);
        $h = [];
        foreach ($options['headers'] ?? [] as $k => $v) { if (is_int($k)) { [$k, $v] = array_map('trim', explode(':', $v, 2)); } $h[strtolower($k)] = $v; }
        if (isset($options['auth_bearer'])) $h['authorization'] = 'Bearer ' . $options['auth_bearer'];
        if (array_key_exists('json', $options)) $h['content-type'] = 'application/json';
        $options['normalized_headers'] = $h;
        $this->appels[] = ['method' => $method, 'url' => $url, 'options' => $options];
        $f = $this->factory;
        if (is_callable($f)) $r = $f($method, $url, $options);
        elseif (is_array($f)) $r = array_shift($this->factory) ?? new MockResponse('', ['http_code' => 500]);
        elseif ($f instanceof MockResponse) $r = clone $f;
        else $r = new MockResponse('', ['http_code' => 200]);
        $r->url = $url; $r->method = $method; $r->options = $options;
        if (self::$echo) { try { $s = $r->getStatusCode(); } catch (\Throwable $e) { $s = 'coupure réseau'; } echo "CLIENT> $method $url → $s\n"; }
        return $r;
    }
}

namespace Symfony\Contracts\Cache;
interface ItemInterface { public function expiresAfter(int|\DateInterval|null $time): static; public function getKey(): string; }
interface CacheInterface { public function get(string $key, callable $callback): mixed; public function delete(string $key): bool; }

namespace Symfony\Component\Cache\Adapter;
use Symfony\Contracts\Cache\{CacheInterface, ItemInterface};
final class CacheItem implements ItemInterface {
    public ?int $ttl = null;
    public function __construct(private string $key) {}
    public function expiresAfter(int|\DateInterval|null $time): static { $this->ttl = $time instanceof \DateInterval ? (new \DateTimeImmutable('@0'))->add($time)->getTimestamp() : $time; return $this; }
    public function getKey(): string { return $this->key; }
}
/** Cache en mémoire. $cache->avancer(secondes) fait avancer son horloge (pour tester l'expiration). */
final class ArrayAdapter implements CacheInterface {
    private array $items = []; private int $now = 0;
    public int $calculs = 0;
    public function get(string $key, callable $callback): mixed {
        if (isset($this->items[$key]) && ($this->items[$key][1] === null || $this->items[$key][1] > $this->now)) return $this->items[$key][0];
        $item = new CacheItem($key); $this->calculs++;
        $v = $callback($item);
        $this->items[$key] = [$v, $item->ttl === null ? null : $this->now + $item->ttl];
        return $v;
    }
    public function delete(string $key): bool { unset($this->items[$key]); return true; }
    public function avancer(int $secondes): void { $this->now += $secondes; }
}
PHPHC);
"""
