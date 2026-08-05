{
  description = "Google Cloud CLI development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:
    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true; # Required for Google Cloud SDK
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            # Legacysyntax for Nixpkgs (circa April 2023)
            (pkgs.google-cloud-sdk.withExtraComponents [
              pkgs.google-cloud-sdk.components.gke-gcloud-auth-plugin
            ])
          ];

          shellHook = ''
            echo "⚡ Google Cloud CLI environment activated!"
            gcloud --version
          '';
        };

      });
}
