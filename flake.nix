{
  description = "Mak's Telegram bot for suggestions";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        tgcrypto = pkgs.python3Packages.buildPythonPackage rec {
          pname = "tgcrypto_pyrofork";
          version = "1.2.8";
          format = "setuptools";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-EGMXssQsxfzXR1pQZH/uLaMEB2zfzSRE9y1SVJJ7Kvo=";
          };

          doCheck = false;
        };

        pyrotgfork = pkgs.python3Packages.buildPythonPackage rec {
          pname = "pyrotgfork";
          version = "2.2.24";
          format = "pyproject";

          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            hash = "sha256-iQUW7IoFWUyWysH9dNP4ylXE3Dg5N/nlUnloQS+Pb94=";
          };

          nativeBuildInputs = with pkgs.python3Packages; [
            hatchling
            setuptools-scm
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            pyaes
            pysocks
            tgcrypto
          ];

          doCheck = false;
        };
        
        # Define python and required libraries
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pyrotgfork
          tgcrypto
          python-dotenv
        ]);
      in
      {
        # package
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "art-suggestion-bot";
          version = "1.0.0";
          src = ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          installPhase = ''
            mkdir -p $out/share/art-suggestion-bot
            cp main.py db.py config.py $out/share/art-suggestion-bot/

            makeWrapper ${pythonEnv}/bin/python $out/bin/art-suggestion-bot \
              --add-flags "$out/share/art-suggestion-bot/main.py"
          '';
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
        };
      })
    ) // {
      nixosModules.default = { config, pkgs, lib, ... }:
        let
          cfg = config.services.art-suggestion-bot;
        in {
          options.services.art-suggestion-bot = {
            enable = lib.mkEnableOption "Python Telegram bot for suggesting posts to linked channel";
            
            environmentFile = lib.mkOption {
              type = lib.types.str;
              description = "Path to .env file for bot";
            };
          };

          config = lib.mkIf cfg.enable {
            systemd.services.art-suggestion-bot = {
              description = "Python Telegram bot for suggesting posts to linked channel";
              after = [ "network.target" ];
              wantedBy = [ "multi-user.target" ];

              serviceConfig = {
                Type = "simple";
                ExecStart = "${self.packages.${pkgs.system}.default}/bin/art-suggestion-bot";
                EnvironmentFile = cfg.environmentFile;
                Restart = "on-failure";
                RestartSec = "5s";
                DynamicUser = true;
                StateDirectory = "art-suggestion-bot";
              };
            };
          };
        };
    };
}
