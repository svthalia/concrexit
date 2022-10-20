{ config, pkgs, lib, ... }:
let

  cfg = config.concrexit-timers;

in
with lib;
{
  options = {
    concrexit-timers.docker-command = mkOption {
      description = "The docker command to use, which runs manage.py";
      type = with types; types.str;
    };
    concrexit-timers.timers = mkOption {
      description = "A timed concrexit command invocation";
      type = with types; attrsOf (submodule {
        options = {
          every = mkOption {
            description = "Run this command every x seconds after concrexit starts";
            type = nullOr int;
            default = null;
          };
          calendar = mkOption {
            description = "See this link on how this is specified: https://www.freedesktop.org/software/systemd/man/systemd.time.html";
            type = nullOr str;
            default = null;
          };
          description = mkOption {
            description = "Description of the timer and service unit";
            type = nullOr str;
            default = null;
          };
        };
      });
    };
  };

  config = {
    assertions = [
      {
        assertion = lists.all (x: (x.calendar == null || x.every == null)) (builtins.attrValues cfg.timers);
        message = "Only `every` or `calendar` is allowed, not both";
      }
    ];
    systemd.services = attrsets.mapAttrs
      (name: value: {
        description = if value.description != null then value.description else "Runs the ${name} concrexit management command";
        after = [ "concrexit.service" ];

        path = with pkgs; [ docker ];
        script = ''
          ${cfg.docker-command} ${name}
        '';

        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = false;
        };
      })
      cfg.timers;

    systemd.timers = attrsets.mapAttrs
      (name: value: {
        enable = true;
        description = if value.description != null then value.description else "Runs the ${name} concrexit management command";
        after = [ "concrexit.service" ];
        requires = [ "concrexit.service" ];
        wantedBy = [ "timers.target" ];
        timerConfig =
          if (value.every != null) then {
            OnUnitInactiveSec = value.every;
            OnBootSec = value.every;
          } else {
            OnCalendar = value.calendar;
          };
      })
      cfg.timers;
  };
}
