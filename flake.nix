{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    friends42 = {
      url = "github:maix0/friends42.git";
      flake = false;
    };
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
      package = rec {
        default = friends42;
        friends42 = with pkgs.python3.pkgs;
          stdenvNoCC.mkDerivation {
            name = "friends42";
            src = inputs.friends42;
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
          stdenvNoCC.mkDerivation {
            name = "updater";
            src = inputs.friends42;
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

      nixosModules = {
        default = {
          pkgs,
          config,
          lib,
          ...
        }:
          with lib; let
            cfg = config.friends42;
          in {
            import = [];

            options.friends42 = {
              package = mkOption {
                type = types.package;
                default = self.package.${system}.friends42;
              };
              updaterPackage = mkOption {
                type = types.package;
                default = self.package.${system}.updater;
              };
              enable = mkEnableOption "friends42";
              listeningPort = types.mkOption {
                type = types.port;
                default = 10000;
                description = "The port the load balencer will be listening on";
              };
              redisPort = types.mkOption {
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
                default = /var/lib/friends42/database.db;
              };
            };

            config = mkIf cfg.enable (let
              mainSystemdUnit = idx: {
                name = "friends42-${idx}";
                wantedBy = ["multi-user.target"];
                requires = ["network.target"];
                after = ["network.target"];
                environment = {
                  F42_PORT = cfg.port + idx;
                  F42_REDIS_PORT = cfg.redisPort;
                  F42_REDIS_HOST = "localhost";
                  F42_BOCAL_KEY = cfg.bocalToken;
                  F42_UPDATE_KEY = cfg.updateToken;
                  F42_DB = cfg.dbPath;
                };
                serviceConfig = {
                  User = "friends42";
                  Group = "nobody";
                  EnvironmentFile = cfg.envFile;
                  ExecStart = "${getBin cfg.package}";
                };
              };
            in {
              users.users.friends42 = {
                isSystemUser = true;
              };
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
                  servers = map (lib.range 1 cfg.instanceCount) (idx: {
                    "localhost:${cfg.port + idx}" = {};
                  });
                  defaultListen = cfg.port;
                };
                enable = true;
              };
              systemd.services =
                {
                  friends42-updater = {
                    name = "friends42-updater";
                    wantedBy = ["multi-user.target"];
                    requires = ["network.target"];
                    after = ["network.target"];
                    environment = {
                      F42_PORT = cfg.port;
                      F42_REDIS_PORT = cfg.redisPort;
                      F42_REDIS_HOST = "localhost";
                      F42_BOCAL_KEY = cfg.bocalToken;
                      F42_UPDATE_KEY = cfg.updateToken;
                      F42_DB = cfg.dbPath;
                    };
                    serviceConfig = {
                      User = "friends42";
                      Group = "nobody";
                      EnvironmentFile = cfg.envFile;
                      ExecStart = "${getBin cfg.UpdaterPackage}";
                    };
                  };
                }
                // (map (lib.range 1 cfg.instanceCount)
                  (idx: {
                    name = "friends42-${idx}";
                    value = mainSystemdUnit idx;
                  }));
            });
          };
      };
    });
}
