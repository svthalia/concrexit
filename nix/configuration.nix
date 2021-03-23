{ config, pkgs, lib, ... }:
let
  # Aliases so other definitions are shorter
  mapAttrsToList = lib.attrsets.mapAttrsToList;
  concatStringsSep = lib.strings.concatStringsSep;

  concrexit-manage = pkgs.writeScriptBin "concrexit-manage" ''
    #!${pkgs.stdenv.shell}

    set -e
    test -f ${cfg.dir}/secrets.env && source ${cfg.dir}/secrets.env
    export MANAGE_PY=1
    ${concatStringsSep "\n" (mapAttrsToList (name: value: "export ${name}=\"\${${name}:-${value}}\"") config.concrexit.env-vars)}
    exec ${pkgs.concrexit}/bin/python ${pkgs.concrexit}/src/website/manage.py $@
  '';
  sudo-concrexit-manage = pkgs.writeScriptBin "sudo-concrexit-manage" ''
    #!${pkgs.stdenv.shell}

    exec /run/wrappers/bin/sudo -E -u concrexit ${concrexit-manage}/bin/concrexit-manage $@
  '';

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

  cfg = config.concrexit;

in
{
  imports = [ ./timed-command.nix ];

  # The options we define here can be applied in any of the included configuration files.
  # The defaults should be good though.
  options = with lib; {
    concrexit.app-port = mkOption {
      type = types.port;
      default = 8000;
    };

    concrexit.domain = mkOption {
      type = types.str;
      default = "staging.thalia.nu";
    };

    concrexit.dir = mkOption {
      type = types.path;
      default = "/var/lib/concrexit";
    };

    concrexit.user = mkOption {
      type = types.str;
      default = "concrexit";
    };

    concrexit.ssl = mkOption {
      type = types.bool;
      default = true;
    };

    concrexit.allowUnknownHost = mkOption {
      type = types.bool;
      default = !cfg.ssl;
      description = "If this option is enabled we allow any hostname to link to Concrexit";
    };

    concrexit.env-vars = mkOption {
      type = types.attrsOf types.str;
      apply = x: {
        SITE_DOMAIN = if cfg.ssl then cfg.domain else "*";
        MEDIA_ROOT = "${cfg.dir}/media";
        SENDFILE_ROOT = "${cfg.dir}/media";
        POSTGRES_USER = "concrexit";
        POSTGRES_DB = "concrexit";
        DJANGO_ENV = "staging";
        DJANGO_EMAIL_HOST = "smtp-relay.gmail.com";
        DJANGO_EMAIL_PORT = "587";
        DJANGO_EMAIL_USE_TLS = "1";
        SEPA_CREDITOR_ID = "NL67ZZZ401464640000";
        GSUITE_MEMBERS_AUTOSYNC = "1";
        GSUITE_ADMIN_USER = "concrexit-admin@thalia.nu";
        GSUITE_DOMAIN = "staging.thalia.nu";
        GSUITE_MEMBERS_DOMAIN = "members.staging.thalia.nu";
        THALIA_PAY_ENABLED = "1";
      } // x;
      default = { };
    };
  };

  config = {
    # Allow the concrexit-manage command to be used as pkgs.concrexit-manage
    nixpkgs.overlays = [
      (_self: _super: {
        inherit concrexit-manage sudo-concrexit-manage;
      })
    ];
    # Install the concrexit-manage command globally
    environment.systemPackages = [ pkgs.sudo-concrexit-manage ];

    security.acme.email = "www@thalia.nu";
    security.acme.acceptTerms = true;

    nix = {
      gc.automatic = true;
      # This is required to be able to use nix-copy-closure
      trustedUsers = [ "root" "deploy" "jelle" "wouter" ];
    };

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

    # This user is used by the GitHub Action to place the new configuration
    users.users.deploy = {
      isNormalUser = true;
      description = "Deploy user";
      extraGroups = [ "wheel" ];
      openssh.authorizedKeys.keys = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICxVTPZp7bOJhmU3hsK6yCSDALTC68/sQ5NRce531XGK deploykey"
      ];
    };

    # Enable the SSH server, this also opens port 22 automatically
    services.openssh.enable = true;

    # Make concrexit user
    users.users.${cfg.user} = { };

    systemd.services = {
      # Create the directory that concrexit uses to place files and the secrets
      # This directory is created by this seperate service because the main service runs as the
      # concrexit user
      concrexit-dir = {
        wantedBy = [ "multi-user.target" ];
        script = ''
          mkdir --parents ${cfg.dir}/media
          chown ${cfg.user} ${cfg.dir}/media
        '';
      };

      # The main systemd service which runs concrexit via uwsgi
      concrexit = {
        after = [ "networking.target" "postgresql.service" "concrexit-dir.service" ];
        wantedBy = [ "multi-user.target" ];

        serviceConfig = {
          User = cfg.user;
          KillSignal = "SIGQUIT";
          Type = "notify";
          TimeoutStartSec = "infinity";
          NotifyAccess = "all";
        };

        script = ''
          if [ -f ${cfg.dir}/secrets.env ]; then
            source ${cfg.dir}/secrets.env
          else
            export SECRET_KEY=$(hostid)
            echo "You should set the secrets in the env file!" >&2
          fi

          export STATIC_ROOT="${pkgs.concrexit}/static"
          export SITE_DOMAIN="${if cfg.ssl then cfg.domain else "*"}"
          export SOURCE_COMMIT="${pkgs.concrexit.name}"

          # Load extra variables from the concrexit.env-vars option
          ${concatStringsSep "\n" (mapAttrsToList (name: value: "export ${name}=\"${value}\"") cfg.env-vars)}

          ${pkgs.concrexit}/bin/concrexit-uwsgi --socket :${toString cfg.app-port}
        '';
      };
    };

    # These configuration options are defined and implemented by the timed-commands.nix file
    concrexit-timers = {
      send_scheduled_messages = {
        every = 60 * 5;
        description = "Send scheduled push notifications";
      };
      sendplannednewsletters = {
        every = 60;
        description = "Send planned newsletters";
      };
      sync_mailinglists.calendar = "*-*-* *:30:00";
      clearsessions.calendar = "*-*-* 23:00:00";
      minimiseregistrations.calendar = "*-*-01 03:00:00";
      delete_gsuite_users.calendar = "*-*-01 03:00:00";
      dataminimisation.calendar = "*-03-01 03:00:00";
      sendexpirationnotification.calendar = "*-08-15 06:00:00";
      sendmembershipnotification.calendar = "*-08-31 06:00:00";
      sendinformationcheck.calendar = "*-10-15 06:00:00";
      revokeoldmandates.calendar = "*-*-* 03:00:00";
    };

    services = {
      nginx = {
        enable = true;

        recommendedGzipSettings = true;
        recommendedOptimisation = true;
        recommendedTlsSettings = true;

        virtualHosts =
          let
            # Because this is used for multiple vhosts below, we just define it once
            # here as a variable
            pizzaConfig = {
              enableACME = cfg.ssl;
              locations."/".return = "301 https://${cfg.domain}/pizzas";
              extraConfig = securityHeaders;
            };
          in
          {
            "${cfg.domain}" = {
              # Request a certificate from letsencrypt
              enableACME = cfg.ssl;
              # Enable redirects to https
              forceSSL = cfg.ssl;
              default = cfg.allowUnknownHost;
              locations."/".extraConfig = ''
                uwsgi_pass 127.0.0.1:${toString cfg.app-port};
              '';
              locations."/.well-known/change-password".return = "301 https://$host/password_change/";
              locations."/static/".alias = "${pkgs.concrexit}/static/";
              locations."/media/public/".alias = "${cfg.dir}/media/public/";
              locations."/media/sendfile/" = {
                alias = "${cfg.dir}/media/";
                extraConfig = "internal;";
              };
              locations."= /maintenance.html" = {
                alias = ../resources/maintenance.html;
                extraConfig = "internal;";
              };
              extraConfig = ''
                error_page 502 /maintenance.html;

                ${securityHeaders}
              '';
            };
            "www.${cfg.domain}" = {
              enableACME = cfg.ssl;
              locations."/".return = "301 https://${cfg.domain}$request_uri";
              extraConfig = securityHeaders;
            };
            "pizza.${cfg.domain}" = pizzaConfig;
            "pasta.${cfg.domain}" = pizzaConfig;
            "xn--vi8h.${cfg.domain}" = pizzaConfig;
            "xn--3i8h.${cfg.domain}" = pizzaConfig;

            # Disallow other Host headers when this server is configured for ssl
            # (so it's not added for local testing in the VM)
            "\"\"" = {
              default = !cfg.allowUnknownHost;
              locations."/".return = "444";
            };
          };
      };

      # Make sure a database exists that is accessible by the concrexit user
      postgresql = {
        enable = true;
        ensureDatabases = [ cfg.user ];
        ensureUsers = [
          {
            name = cfg.user;
            ensurePermissions = {
              "DATABASE ${cfg.user}" = "ALL PRIVILEGES";
            };
          }
        ];
      };
    };

    # These open the web ports, the SSH port is opened automatically
    networking.firewall.allowedTCPPorts = [ 80 443 ];
  };
}
