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
        ];
      };
      packages = rec {
        default = friends42;
        friends42 = with pkgs.python3.pkgs;
          pkgs.stdenvNoCC.mkDerivation {
            name = "friends42";
            src = ./.;
            installPhase = ''
              mkdir -p $out/opt
              cp -farT . $out/opt

              mkdir -p $out/bin
              cat <<EOF >$out/bin/friends42
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
              chmod +x $out/bin/friends42
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
            cfg = config.services.friends42;
          in {
            options.services.friends42 = {
              package = mkOption {
                type = types.package;
                default = self.packages.${pkgs.system}.friends42;
              };
              updaterPackage = mkOption {
                type = types.package;
                default = self.packages.${pkgs.system}.updater;
              };
              enable = mkEnableOption "friends42";
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
                default = "/var/lib/friends42/database.db";
              };
              domain = mkOption {
                type = types.str;
                description = "domain to be used";
                default = "localhost";
              };
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
                  User = "friends42";
                  Group = "nobody";
                  EnvironmentFile = "/env";
                  ExecStart = "${cfg.package}/bin/friends42";
                };
              };
            in {
              containers.friends42 = {
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
                  networking.firewall.allowedTCPPorts = [cfg.port];
                  system.activationScripts.friends42 = lib.stringAfter ["var"] ''
                    mkdir -p /var/lib/friends42
                    chown friends42 /var/lib/friends42
                  '';

                  users.users.friends42 = {
                    isSystemUser = true;
                    group = "friends42";
                  };
                  users.groups.friends42 = {};
                  services.redis.servers.friends42 = {
                    user = "friends42";
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
                  systemd.services =
                    {
                      friends42-updater = {
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
                          User = "friends42";
                          Group = "nobody";
                          EnvironmentFile = "/env";
                          ExecStart = "${getBin cfg.updaterPackage}/bin/updater";
                        };
                      };
                    }
                    // (listToAttrs (map
                      (idx: {
                        name = "friends42-${toString idx}";
                        value = mainSystemdUnit idx;
                      }) (lib.range 1 cfg.instanceCount)));
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
            services.friends42 = {
              enable = true;
              bocalToken = "bocal";
              updateToken = "update";
              envFile = "/etc/envfile";
              domain = "fft.maix.me";
              port = 80;
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
