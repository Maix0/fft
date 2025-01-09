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
                privateNetwork = true;
                bindMounts = {
                  "/env" = {
                    hostPath = "${cfg.envFile}";
                    isReadOnly = true;
                  };
                };
                autoStart = true;
                forwardPorts = [
                  {
                    containerPort = 80;
                    hostPort = cfg.port;
                    protocol = "tcp";
                  }
                ];
                config = {
                  system.activationScripts.makeVaultWardenDir = lib.stringAfter ["var"] ''
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
                    upstreams.friends42 = {
                      extraConfig = ''
                        ip_hash;
                      '';
                      servers = builtins.foldl' (a: b: a // b) {} (map (idx: {
                        "localhost:${toString (10000 + idx)}" = {};
                      }) (lib.range 1 cfg.instanceCount));
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
                          F42_PORT = toString 80;
                          F42_REDIS_PORT = toString cfg.redisPort;
                          F42_REDIS_HOST = "localhost";
                          F42_BOCAL_KEY = cfg.bocalToken;
                          F42_UPDATE_KEY = cfg.updateToken;
                          F42_DB = cfg.dbPath;
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
            services.friends42 = {
              enable = true;
              bocalToken = "bocal";
              updateToken = "update";
              envFile = "/etc/envfile";
            };
          })
          ({
            pkgs,
            lib,
            ...
          }: {
            virtualisation.vmVariant = {
              users.users.root.password = "root";
              users.users.nixos = {
                password = "nixos";
                isNormalUser = true;
                home = "/home/nixos";
              };
              virtualisation = {
                memorySize = 8096;
                cores = 8;
                graphics = false;
                diskSize = 16000; # 32 Gb
              };
            };
          })
        ];
      };
    };
}
