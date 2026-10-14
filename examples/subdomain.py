import sys

from digitalocean_sdk import DigitalOcean, NotFoundError


def main() -> None:
    if len(sys.argv) != 4:
        print("usage: python subdomain.py <domain> <name> <ip>")
        sys.exit(1)

    domain, name, ip = sys.argv[1:]
    with DigitalOcean() as do:
        try:
            current = do.dns.list(domain, "A", name)
        except NotFoundError:
            print(f"{domain} is not in this DigitalOcean account")
            sys.exit(1)

        if [record.data for record in current] == [ip]:
            print(f"{name}.{domain} already points to {ip}")
            return

        do.dns.point(domain, name, ip)
        print(f"{name}.{domain} now points to {ip}")


if __name__ == "__main__":
    main()
