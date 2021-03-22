{ config, pkgs, lib, ... }:
let

  cfg = config.concrexit-timers;

in
with lib;
{
  options = {
    concrexit-timers = mkOption {
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
        assertion = lists.all (x: (x.calendar == null || x.every == null)) (builtins.attrValues cfg);
        message = "Only `every` or `calendar` is allowed, not both";
      }
    ];
    systemd.services = attrsets.mapAttrs
      (name: value: {
        description = if value.description != null then value.description else "Runs the ${name} concrexit management command";
        after = [ "concrexit.service" ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = false;
          ExecStart = "${pkgs.concrexit-manage}/bin/concrexit-manage ${name}";
          User = config.concrexit.user;
        };
      })
      cfg;

    systemd.timers = attrsets.mapAttrs
      (name: value: {
        enable = true;
        description = if value.description != null then value.description else "Runs the ${name} concrexit management command";
        after = [ "concrexit.service" ];
        wantedBy = [ "timers.target" ];
        timerConfig =
          if (value.every != null) then {
            OnUnitInactiveSec = value.every;
            OnBootSec = value.every;
          } else {
            OnCalendar = value.calendar;
          };
      })
      cfg;
  };
}
