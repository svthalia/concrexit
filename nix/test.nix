{ ... }:
{
  name = "concrexit";

  machine = { ... }: {
    imports = [ ./configuration.nix ];

    concrexit.ssl = false;
  };

  testScript = { nodes }: ''
    def remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix) :]
        return text


    machine.wait_for_unit("concrexit.service")
    machine.wait_for_open_port(80)
    machine.wait_for_open_port(${toString nodes.machine.config.concrexit.app-port})

    machine.succeed("GSUITE_MEMBERS_AUTOSYNC=0 concrexit-manage createfixtures -a 2>&1")

    import xml.etree.ElementTree as ET
    import os.path

    machine.succeed("curl --fail 'http://localhost/'")

    sitemap_xml = machine.succeed("curl --fail 'http://localhost/sitemap.xml'")
    root = ET.fromstring(sitemap_xml)
    urls = []
    for child in root:
        url = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        urls.append(url.text)

    # Only get one url per boring suffix (e.g. only one event etc.)
    urls = sorted(sorted((url, len(url.split("/"))) for url in urls), key=lambda x: x[1])
    last_url = urls[0]
    for url in urls[1:]:
        if last_url[1] == url[1] and re.fullmatch(
            r"[\d\-]+",
            remove_prefix(url[0], os.path.commonprefix([url[0], last_url[0]])).strip("/"),
        ):
            continue
        machine.succeed(f"curl --fail '{url[0]}'")
        last_url = url
  '';
}
