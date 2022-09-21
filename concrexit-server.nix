{ config, pkgs, nixpkgs, lib, ... }:
let
  hostName = config.networking.hostName;
  production = hostName == "production";

  productionEnvFile = ./infra/docker/production/concrexit-production-public.env;
  stagingEnvFile = ./infra/docker/staging/concrexit-staging-public.env;
  envFile = if production then productionEnvFile else stagingEnvFile;

  productionSecrets = ./infra/secrets/concrexit-production.env.age;
  stagingSecrets = ./infra/secrets/concrexit-staging.env.age;
  secretsFile = if production then productionSecrets else stagingSecrets;

  dockerImage = "ghcr.io/svthalia/concrexit:${if production then "latest" else "master"}";

  staticdir = "/var/lib/concrexit/static/";
  mediadir = "/var/lib/concrexit/media/";
  domain = "thalia.nu";

  securityHeaders = ''
    # X-Frame-Options tells the browser whether you want to allow your site to be framed or not.
    # By preventing a browser from framing your site you can defend against attacks like clickjacking.
    add_header X-Frame-Options SAMEORIGIN;
    # X-Content-Type-Options stops a browser from trying to MIME-sniff the content type and forces it to stick with the declared content-type.
    add_header X-Content-Type-Options nosniff;
    # X-XSS-Protection sets the configuration for the cross-site scripting filters built into most browsers.
    add_header X-XSS-Protection "1; mode=block";
    # HTTP Strict Transport Security is an excellent feature to support on your site and strengthens your implementation of TLS by getting the User Agent to enforce the use of HTTPS.
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    # Feature Policy is a new header that allows a site to control which features and APIs can be used in the browser.
    add_header Feature-Policy "camera 'none'; vr 'none'; camera 'none'; accelerometer 'none'; gyroscope 'none'";
    # Referrer Policy is a new header that allows a site to control how much information the browser includes with navigations away from a document and should be set by all sites.
    add_header Referrer-Policy strict-origin;
    # The Expect-CT header allows sites to opt in to reporting and/or enforcement of Certificate Transparency requirements,
    # which prevents the use of misissued certificates for that site from going unnoticed.
    # enforce not added for now
    add_header Expect-CT "max-age=604800";
  '';
in
{
  nix = {
    gc.automatic = true;
  };

  networking = {
    domain = "thalia.nu";
  };

  security.acme.defaults.email = "www@thalia.nu";
  security.acme.acceptTerms = true;

  # Allow passwordless sudo for easier deployment
  security.sudo.wheelNeedsPassword = false;

  # Users are purely defined by this configuration file, so password changes
  # will be reset when a new version is deployed
  users.mutableUsers = false;
  users.users.jelle = {
    isNormalUser = true;
    description = "Jelle Besseling";
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICunYiTe1MOJsGC5OBn69bewMBS5bCCE1WayvM4DZLwE jelle@Jelles-Macbook-Pro.local"
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID+/7ktPyg4lYL0b6j3KQqfVE6rGLs5hNK3Q175th8cq jelle@foon"
    ];
  };
  users.users.wouter = {
    isNormalUser = true;
    description = "Wouter Doeland";
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEblHIN5uaooHczkiqbXa6V7H7bfhgGTVLKA0sUggBkP wouter@wouterdoeland.nl"
    ];
  };

  # Enable the SSH server, this also opens port 22 automatically
  services.openssh.enable = true;

  virtualisation.docker.enable = true;

  age.secrets = {
    "concrexit-secrets.env".file = secretsFile;
  };

  systemd.services.concrexit-network = {
    wantedBy = [ "multi-user.target" ];
    requires = [ "docker.service" ];
    after = [ "docker.service" ];

    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };

    path = with pkgs; [ docker ];
    script = ''
      docker network create concrexit || true
    '';
  };

  systemd.services.postgres = {
    wantedBy = [ "multi-user.target" ];
    requires = [ "docker.service" "concrexit-network.service" ];
    after = [ "docker.service" "concrexit-network.service" ];

    path = with pkgs; [ docker ];
    script = ''
      docker rm postgres || true
      docker run --name postgres \
        -e POSTGRES_USER=concrexit \
        -e POSTGRES_PASSWORD=concrexit \
        -e PGDATA=/var/lib/postgresql/data/pgdata \
        -v /volume/concrexit_postgres:/var/lib/postgresql/data \
        --network concrexit  postgres:11.17-bullseye
    '';
  };

  systemd.services.concrexit-static = {
    wantedBy = [ "multi-user.target" ];
    requires = [ "docker.service" ];
    after = [ "docker.service" ];

    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
    };

    path = with pkgs; [ docker ];
    script = ''
      docker pull ${dockerImage}
      docker run --rm --network concrexit --name concrexit-static \
        -v /var/lib/concrexit/static:/static \
        --env-file ${envFile} \
        --env-file ${config.age.secrets."concrexit-secrets.env".path} \
        ${dockerImage} /app/collect-static.sh
    '';
  };

  systemd.services.concrexit = {
    wantedBy = [ "multi-user.target" ];
    requires = [ "postgres.service" "concrexit-static.service" ];
    after = [ "postgres.service" "concrexit-static.service" ];

    path = with pkgs; [ docker ];
    script = ''
      docker rm concrexit || true
      docker pull ${dockerImage}
      docker run --network concrexit --name concrexit -p 127.0.0.1:8000:8000 \
        -v /var/lib/concrexit/static:/static \
        -v /var/lib/concrexit/media:/media \
        --env-file ${envFile} \
        --env-file ${config.age.secrets."concrexit-secrets.env".path} \
        ${dockerImage}
    '';
  };

  concrexit-timers = {
    docker-command = ''
      docker run --network concrexit --name concrexit -p 127.0.0.1:8000:8000 \
        -v /var/lib/concrexit/static:/static \
        -v /var/lib/concrexit/media:/media \
        --env-file ${envFile} \
        --env-file ${config.age.secrets."concrexit-secrets.env".path} \
        --entrypoint /app/website/manage.py \
        ${dockerImage}
    '';
    timers = {
      send_scheduled_messages = {
        every = 60 * 5;
        description = "Send scheduled push notifications";
      };
      sendplannednewsletters = {
        every = 60 * 5;
        description = "Send planned newsletters";
      };
      sync_mailinglists.calendar = "*-*-* *:30:00";
      conscribosync.calendar = "*-*-* 23:15:00";
      clearsessions.calendar = "*-*-* 23:00:00";
      minimiseregistrations.calendar = "*-*-01 03:00:00";
      delete_gsuite_users.calendar = "*-*-01 03:00:00";
      dataminimisation.calendar = "*-*-* 03:00:00";
      sendexpirationnotification.calendar = "*-08-15 06:00:00";
      sendmembershipnotification.calendar = "*-08-31 06:00:00";
      sendinformationcheck.calendar = "*-10-15 06:00:00";
      sendpromorequestoverview.calendar = "Mon *-*-* 08:00:00";
      revokeoldmandates.calendar = "*-*-* 03:00:00";
      revoke_staff.calendar = "*-*-* 03:00:00";
      cleartokens.calendar = "*-*-* 03:00:00";
    };
  };

  systemd.tmpfiles.rules = [
    "d /var/lib/concrexit/ 0755 root root - -"
  ];

  services.nginx = {
    enable = true;

    recommendedGzipSettings = true;
    recommendedOptimisation = true;
    recommendedTlsSettings = true;
    recommendedProxySettings = true;

    clientMaxBodySize = "2G";

    commonHttpConfig = ''
      log_format logfmt 'time="$time_local" client=$remote_addr '
          'method=$request_method url="$request_uri" '
          'request_length=$request_length '
          'status=$status bytes_sent=$bytes_sent '
          'body_bytes_sent=$body_bytes_sent '
          'referer=$http_referer '
          'user_agent="$http_user_agent" '
          'upstream_addr=$upstream_addr '
          'upstream_status=$upstream_status '
          'request_time=$request_time '
          'upstream_response_time=$upstream_response_time '
          'upstream_connect_time=$upstream_connect_time '
          'upstream_header_time=$upstream_header_time';
    '';

    virtualHosts =
      let
        # Because this is used for multiple vhosts below, we just define it once
        # here as a variable
        pizzaConfig = {
          enableACME = production;
          addSSL = production;
          locations."/".return = "301 https://${domain}/pizzas";
          extraConfig = securityHeaders;
        };
      in
      {
        "${domain}" = {
          # Request a certificate from letsencrypt
          enableACME = production;
          # Enable redirects to https
          forceSSL = production;
          default = !production;
          locations."/".extraConfig = ''
            proxy_pass http://127.0.0.1:8000;
          '';
          locations."/static/" = {
            alias = staticdir;
            # We add not only the cache header but also the security headers again
            # This is because nginx replaces all the previous set add_header directives
            # if you add one to a lower level (location is lower than server)
            # see https://github.com/yandex/gixy/blob/master/docs/en/plugins/addheaderredefinition.md
            extraConfig = ''
              add_header Cache-Control "public, max-age=31536000, immutable";
              ${securityHeaders}
            '';
          };
          locations."/media/public/".alias = "${mediadir}/public/";
          locations."/media/sendfile/" = {
            alias = mediadir;
            extraConfig = "internal;";
          };
          locations."= /.well-known/apple-app-site-association" = {
            alias = ./infra/resources/apple-app-site-association.json;
            extraConfig = "default_type application/json;";
          };
          locations."/.well-known/change-password" = {
            # Implementing https://github.com/WICG/change-password-url
            return = "301 https://$host/user/password_change/";
          };
          locations."= /.well-known/security.txt" = {
            # Implementing https://tools.ietf.org/html/draft-foudil-securitytxt-12
            alias = ./infra/resources/security.txt;
            extraConfig = "default_type text/plain;";
          };
          locations."= /security.txt" = {
            # Implementing https://tools.ietf.org/html/draft-foudil-securitytxt-12
            alias = ./infra/resources/security.txt;
            extraConfig = "default_type text/plain;";
          };
          locations."= /pgp-key.txt" = {
            alias = ./infra/resources/pgp-key.txt;
            extraConfig = "default_type text/plain;";
          };
          locations."= /maintenance.html" = {
            alias = ./infra/resources/maintenance.html;
            extraConfig = "internal;";
          };
          extraConfig = ''
            error_page 502 /maintenance.html;
            access_log /var/log/nginx/concrexit.access.log logfmt;

            ${securityHeaders}
          '';
        };
        "www.${domain}" = {
          enableACME = production;
          addSSL = production;
          locations."/".return = "301 https://${domain}$request_uri";
          extraConfig = securityHeaders;
        };
        "pizza.${domain}" = pizzaConfig;
        "xn--vi8h.${domain}" = pizzaConfig;
        "alumni.${domain}" = {
          enableACME = production;
          addSSL = production;
          locations."/".return = "301 https://${domain}/association/alumni/";
          extraConfig = securityHeaders;
        };

        # Disallow other Host headers when this server is configured for ssl
        # (so it's not added for local testing in the VM)
        "\"\"" = {
          default = production;
          locations."/".return = "444";
          extraConfig = ''
            access_log off;
          '';
        };
      };
  };

  systemd.services.swapfile = {
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
    };

    path = with pkgs; [ utillinux ];

    script = ''
      if cat /proc/swaps | grep -v '^Filename' > /dev/null; then
        exit 0
      fi
      if [ ! -d "/var/swap" ]; then
        mkdir /var/swap
      fi
      if [ ! -e "/var/swap/swapfile_2GiB" ]; then
        fallocate -l 2GiB "/var/swap/swapfile_2GiB"
        mkswap "/var/swap/swapfile_2GiB"
      fi
      swapon "/var/swap/swapfile_2GiB"
    '';
  };

  # These open the web ports, the SSH port is opened automatically
  networking.firewall.allowedTCPPorts = [ 80 443 ];

  system.stateVersion = "22.05";
}
