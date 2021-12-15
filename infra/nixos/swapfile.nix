{ config, pkgs, lib, ... }:
let

  cfg = config.swapfile;

in
with lib;
{
  options = {
    swapfile = {
      enable = mkEnableOption "Swapfile";

      size = mkOption {
        description = "Size of the swapfile to allocate if it doesn't exist yet";
        type = types.nullOr types.str;
        default = "2GiB";
      };
    };
  };

  config = {
    systemd.services.swapfile = mkIf cfg.enable {
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
        if [ ! -e "/var/swap/swapfile_${cfg.size}" ]; then
          fallocate -l ${cfg.size} "/var/swap/swapfile_${cfg.size}"
          mkswap "/var/swap/swapfile_${cfg.size}"
        fi

        swapon "/var/swap/swapfile_${cfg.size}"
      '';
    };
  };
}
