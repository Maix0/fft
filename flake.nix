{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShell = pkgs.mkShellNoCC {
        packages = [
          (with pkgs.python3.pkgs;
            python.withPackages (pypkgs:
              with pypkgs; [
                redis
                flask
                requests
                arrow
                sentry-sdk
              ]))
          pkgs.black
          pkgs.ruff
        ];
      };
      packages = rec {
        default = fft;
        fft = with pkgs.python3.pkgs;
          pkgs.stdenvNoCC.mkDerivation {
            name = "fft";
            src = ./.;
            installPhase = ''
              mkdir -p $out/opt
              cp -farT . $out/opt

              mkdir -p $out/bin
              cat <<EOF >$out/bin/fft
              #!/bin/sh
              cd $out/opt
              exec ${python.withPackages (pypkgs:
                with pypkgs; [
                  redis
                  flask
                  requests
                  arrow
                  sentry-sdk
                ])}/bin/python ./app.py
              EOF
              chmod +x $out/bin/fft
            '';
          };
        updater = with pkgs.python3.pkgs;
          pkgs.stdenvNoCC.mkDerivation {
            name = "updater";
            src = ./.;
            installPhase = ''
              mkdir -p $out/opt
              cp -farT . $out/opt

              mkdir -p $out/bin
              cat <<EOF >$out/bin/updater
              #!/bin/sh
              cd $out/opt
              exec ${python.withPackages (pypkgs:
                with pypkgs; [
                  redis
                  flask
                  requests
                  arrow
                  sentry-sdk
                ])}/bin/python ./updater.py
              EOF
              chmod +x $out/bin/updater
            '';
          };
      };
    })
    // {
      nixosModules = {
        default = {
          pkgs,
          config,
          lib,
          ...
        }:
          with lib; let
            cfg = config.services.fft;
          in {
            options.services.fft = {
              package = mkOption {
                type = types.package;
                default = self.packages.${pkgs.system}.fft;
              };
              updaterPackage = mkOption {
                type = types.package;
                default = self.packages.${pkgs.system}.updater;
              };
              enable = mkEnableOption "fft";
              port = mkOption {
                type = types.port;
                default = 10000;
                description = "The port the load balencer will be listening on";
              };
              redisPort = mkOption {
                type = types.port;
                default = 9999;
                description = "The port the load balencer will be listening on";
              };
              instanceCount = mkOption {
                type = types.ints.positive;
                default = 1;
                description = "The number of instance that will be running";
              };
              envFile = mkOption {
                type = types.path;
                description = "Environment file";
              };
              bocalToken = mkOption {
                type = types.strMatching "[a-zA-Z0-9_\-]+";
                description = "Bocal Token";
              };
              updateToken = mkOption {
                type = types.strMatching "[a-zA-Z0-9_\-]+";
                description = "Update Token";
              };
              dbPath = mkOption {
                type = types.path;
                description = "database Path";
                default = "/var/lib/fft/database.db";
              };
              domain = mkOption {
                type = types.str;
                description = "domain to be used";
                default = "localhost";
              };
              backup = {
                enable = mkEnableOption "Backup of database";
                timer = mkOption {
                  type = types.attrsOf types.str;
                  description = "will be merged into a systemd.timers.<name>.timerConfig";
                  default = {
                    "OnUnitActiveSec" = "1d";
                    "OnBootSec" = "1d";
                  };
                };
                backupDir = mkOption {
                  type = types.path;
                  description = "Where the backup will be stored";
                  default = "/var/lib/fft-backup/";
                };
                backupCount = mkOption {
                  type = types.ints.positive;
                  default = 5;
                  description = "Number of stored backup";
                };
              };
              description = "Backup the database";
            };

            config = mkIf cfg.enable (let
              mainSystemdUnit = idx: {
                wantedBy = ["multi-user.target"];
                requires = ["network.target"];
                after = ["network.target"];
                enable = true;
                environment = {
                  F42_PORT = toString (10000 + idx);
                  F42_REDIS_PORT = toString cfg.redisPort;
                  F42_REDIS_HOST = "localhost";
                  F42_BOCAL_KEY = cfg.bocalToken;
                  F42_UPDATE_KEY = cfg.updateToken;
                  F42_DB = cfg.dbPath;
                  F42_DOMAIN = cfg.domain;
                };
                serviceConfig = {
                  User = "fft";
                  Group = "nobody";
                  EnvironmentFile = "/env";
                  ExecStart = "${cfg.package}/bin/fft";
                };
              };
            in {
              systemd = mkIf cfg.backup.enable {
                services.fft-backup = {
                  wantedBy = ["multi-user.target"];
                  requires = ["network.target"];
                  after = ["network.target"];
                  enable = true;
                  script = ''
                    TEMP_FILE=$(mktemp)

                    ${
                      concatStringsSep "\n" (lib.reverseList
                        (map
                          (idx: ''
                            if [ -f ${lib.escapeShellArg "${cfg.backup.backupDir}/backup-${toString idx}.sq3"} ]; then
                                ${pkgs.coreutils}/bin/touch -r ${lib.escapeShellArg "${cfg.backup.backupDir}/backup-${toString idx}.sq3"} "$TEMP_FILE"
                                mv ${lib.escapeShellArg "${cfg.backup.backupDir}/backup-${toString idx}.sq3"} ${lib.escapeShellArg "${cfg.backup.backupDir}/backup-${toString (idx + 1)}.sq3"};
                                ${pkgs.coreutils}/bin/touch -r "$TEMP_FILE" ${lib.escapeShellArg "${cfg.backup.backupDir}/backup-${toString idx}.sq3"}
                            fi
                          '')
                          (lib.range 0 (cfg.backup.backupCount - 1))))
                    }
                      until [ -f "/var/lib/nixos-containers/fft/${cfg.dbPath}" ]; do
                        echo "Unable to find the database, sleeping for 30s...";
                        sleep 30;
                      done;
                      ${pkgs.sqlite}/bin/sqlite3 /var/lib/nixos-containers/fft/var/lib/fft/database.db ".backup "${lib.escapeShellArg "${cfg.backup.backupDir}"}/backup-0.sq3
                  '';
                };
                timers.fft-backup = {
                  enable = true;
                  wantedBy = ["multi-user.target"];
                  requires = ["network.target"];
                  after = ["network.target"];
                  timerConfig = cfg.backup.timer;
                };
              };
              system.activationScripts.fft = mkIf cfg.backup.enable (lib.stringAfter ["var"] ''
                mkdir -p ${lib.escapeShellArg cfg.backup.backupDir}
              '');

              containers.fft = {
                privateNetwork = false; # TODO: maybe change it ?
                bindMounts = {
                  "/env" = {
                    hostPath = "${cfg.envFile}";
                    isReadOnly = true;
                  };
                  "/etc/resolv.conf" = {
                    hostPath = "/etc/resolv.conf";
                    isReadOnly = true;
                  };
                };
                autoStart = true;
                hostAddress = "192.168.100.2";
                config = {
                  system.stateVersion = "24.11";
                  networking.firewall.allowedTCPPorts = [cfg.port];
                  system.activationScripts.fft = lib.stringAfter ["var"] ''
                    mkdir -p /var/lib/fft
                    chown fft /var/lib/fft
                  '';

                  users.users.fft = {
                    isSystemUser = true;
                    group = "fft";
                  };
                  users.groups.fft = {};
                  services.redis.servers.fft = {
                    user = "fft";
                    port = cfg.redisPort;
                    enable = true;
                  };
                  services.nginx = {
                    upstreams."${cfg.domain}" = {
                      extraConfig = ''
                      '';
                      servers = builtins.foldl' (a: b: a // b) {} (map (idx: {
                        "127.0.0.1:${toString (10000 + idx)}" = {};
                      }) (lib.range 1 cfg.instanceCount));
                    };
                    virtualHosts."${cfg.domain}" = {
                      locations = {
                        "/" = {
                          proxyPass = "http://${cfg.domain}";
                        };
                      };
                      listen = [
                        {
                          addr = "0.0.0.0";
                          port = cfg.port;
                        }
                      ];
                      default = true;
                    };
                    enable = true;
                  };
                  systemd = {
                    services =
                      {
                        fft-updater = {
                          wantedBy = ["multi-user.target"];
                          requires = ["network.target"];
                          after = ["network.target"];
                          enable = true;
                          environment = {
                            F42_PORT = toString cfg.port;
                            F42_REDIS_PORT = toString cfg.redisPort;
                            F42_REDIS_HOST = "localhost";
                            F42_BOCAL_KEY = cfg.bocalToken;
                            F42_UPDATE_KEY = cfg.updateToken;
                            F42_DB = cfg.dbPath;
                            F42_DOMAIN = cfg.domain;
                          };
                          serviceConfig = {
                            User = "fft";
                            Group = "nobody";
                            EnvironmentFile = "/env";
                            ExecStart = "${getBin cfg.updaterPackage}/bin/updater";
                          };
                        };

                        fft-update-tutors = {
                          wantedBy = ["multi-user.target"];
                          requires = ["network.target"];
                          after = ["network.target"];
                          enable = true;
                          script = ''
                            ${pkgs.curl}/bin/curl -L http://127.0.0.1/admin/update_tutors/${lib.escapeShellArg cfg.updateToken}
                          '';
                          environment = {
                            F42_DOMAIN = cfg.domain;
                          };
                        };
                      }
                      // (listToAttrs (map
                        (idx: {
                          name = "fft-${toString idx}";
                          value = mainSystemdUnit idx;
                        }) (lib.range 1 cfg.instanceCount)));

                    timers.fft-update-tutors = {
                      enable = true;
                      wantedBy = ["multi-user.target"];
                      requires = ["network.target"];
                      after = ["network.target" "fft-1.service"];
                      timerConfig = {
                        "OnUnitActiveSec" = "1d";
                        "OnBootSec" = "20m";
                      };
                    };
                  };
                };
              };
            });
          };
      };

      nixosConfigurations.test-vm = nixpkgs.lib.nixosSystem rec {
        system = "x86_64-linux";
        modules = [
          ./create-envfile.nix
          self.nixosModules.default
          ({
            pkgs,
            lib,
            ...
          }: {
            networking.firewall.extraCommands = ''
              iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o eth0 -j MASQUERADE
            '';
            services.fft = {
              enable = true;
              bocalToken = "bocal";
              updateToken = "update";
              envFile = "/etc/envfile";
              domain = "fft.maix.me";
              port = 80;
              backup = {
                enable = true;
                timer = {
                  "OnUnitActiveSec" = "1m";
                  "OnBootSec" = "1m";
                };
              };
            };
          })
          ({
            pkgs,
            lib,
            ...
          }: {
            virtualisation.vmVariant = {
              services.openssh.enable = true;
              services.openssh.settings.PermitRootLogin = "yes";
              users.users.root = {
                password = "root";
                openssh.authorizedKeys.keys = [
                  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDQ+u6AcgPYW+4qOQWd5pQec/f+ukOnpVECPiPrYzM/D maix@XeMaix"
                ];
              };
              virtualisation.qemu.networkingOptions = [
                "-device e1000,netdev=net0 -netdev user,id=net0,hostfwd=tcp::5555-:22,\${QEMU_NET_OPTS:+,$QEMU_NET_OPTS}"
              ];

              users.users.maiboyer = {
                autoSubUidGidRange = true;
                createHome = true;
                isNormalUser = true;
                initialHashedPassword = lib.mkForce null;
                group = "maiboyer";
                home = "/home/maiboyer";
                openssh.authorizedKeys.keys = ["ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDQ+u6AcgPYW+4qOQWd5pQec/f+ukOnpVECPiPrYzM/D maix@XeMaix"];
                password = "1234";
                extraGroups = ["wheel" "docker"];
              };
              environment = {
                systemPackages = with pkgs; [
                  docker
                  firefox
                  git
                  bat
                  gnumake
                  kitty
                ];
              };
              users.groups.maiboyer = {};
              security.sudo.wheelNeedsPassword = false;
              users.users.nixos = {
                password = "nixos";
                isNormalUser = true;
                home = "/home/nixos";
              };
              networking.hosts = {"127.0.0.1" = ["fft.maix.me"];};
              services.xserver = {
                enable = true;
                displayManager.gdm.enable = true;
                desktopManager.gnome.enable = true;
              };
              virtualisation = {
                memorySize = 8096;
                cores = 8;
                graphics = true;
                diskSize = 16000; # 32 Gb
              };
            };
          })
        ];
      };
    };
}
