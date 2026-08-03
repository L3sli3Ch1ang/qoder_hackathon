{
  description = "Unified Hackathon Stack: Qoder Desktop + Qoder CLI + FastAPI + Bun + Qdrant (NixOS 26.05)";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
    
    # Numtide's AI flake
    llm-agents.url = "github:numtide/llm-agents.nix";
    llm-agents.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, llm-agents, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true; 
        };

        # Complete runtime library matrix for patching the Electron binary
        runtimeDeps = with pkgs; [
          stdenv.cc.cc.lib
          glib
          nss
          nspr
          atk
          at-spi2-atk
          at-spi2-core
          cups
          dbus
          gtk3
          pango
          cairo
          libdrm
          mesa
          libgbm
          xorg.libxcb
          expat
          libxkbcommon
          alsa-lib
          systemd
          libx11
          libxcomposite
          libxdamage
          libxext
          libxfixes
          libxrandr
          libxrender
          libxtst
          libxscrnsaver
          libuuid
          libsecret
        ];

        libPath = pkgs.lib.makeLibraryPath runtimeDeps;

        # Custom isolated derivation to unpack and patch the raw desktop debian payload
        qoder-desktop = pkgs.stdenv.mkDerivation {
          pname = "qoder-desktop";
          version = "1.0.0";

          # Expects the official installer binary package payload in the active directory
          src = ./qoder_amd64.deb;

          nativeBuildInputs = with pkgs; [ 
            binutils 
            dpkg 
            makeWrapper 
            patchelf 
            glib
            gsettings-desktop-schemas
            gtk3
          ];

          dontBuild = true;
          dontConfigure = true;

          unpackPhase = ''
            runHook preUnpack
            # Extract while completely stripping SetUID root user access blocks
            dpkg-deb --fsys-tarfile $src | tar xf - --no-same-permissions --no-same-owner
            runHook postUnpack
          '';

          installPhase = ''
            runHook preInstall
            
            mkdir -p $out/bin $out/opt $out/share
            
            if [ -d opt ]; then
              cp -r opt/* $out/opt/
            elif [ -d usr/lib ]; then
              cp -r usr/lib/* $out/opt/
            elif [ -d usr/share ]; then
              cp -r usr/share/* $out/opt/
            else
              mkdir -p $out/opt/qoder
              find . -maxdepth 1 -type f -not -name "*.deb" -exec cp {} $out/opt/qoder/ \;
            fi

            MAIN_EXEC=$(find $out/opt -type f -executable \( -name "qoder" -o -name "qoder-desktop" \) | head -n 1)

            if [ -z "$MAIN_EXEC" ]; then
              MAIN_EXEC=$(find $out/opt -type f -executable ! -name "*.so*" ! -name "*.json" ! -name "*.desktop" ! -name "*.sh" ! -name "*crashpad*" | head -n 1)
            fi

            if [ -z "$MAIN_EXEC" ]; then
              echo "Error: Could not locate primary executable binary in package payload."
              exit 1
            fi

            APP_DIR=$(dirname "$MAIN_EXEC")

            if patchelf --print-interpreter "$MAIN_EXEC" >/dev/null 2>&1; then
              patchelf \
                --set-interpreter "$(cat $NIX_CC/nix-support/dynamic-linker)" \
                --set-rpath "${libPath}:\$ORIGIN" \
                "$MAIN_EXEC"
            fi

            makeWrapper "$MAIN_EXEC" $out/bin/qoder-desktop \
              --prefix LD_LIBRARY_PATH : "${libPath}:\$ORIGIN:$APP_DIR" \
              --prefix XDG_DATA_DIRS : "${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}:${pkgs.gtk3}/share/gsettings-schemas/${pkgs.gtk3.name}:\$XDG_DATA_DIRS" \
              --add-flags "--ozone-platform=wayland --enable-features=UseOzonePlatform"

            if [ -d usr/share ]; then
              cp -r usr/share/* $out/share/ 2>/dev/null || true
            fi

            runHook postInstall
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            qoder-desktop
            llm-agents.packages.${system}.qoder-cli
            pkgs.jetbrains.webstorm
            pkgs.jetbrains.pycharm-oss
            pkgs.bun
            pkgs.nodejs_22
            pkgs.uv
            pkgs.python313
            pkgs.sqlite
            pkgs.qdrant
          ];

          shellHook = ''
            echo "🛡️ Stable Hackathon Environment Loaded (NixOS 26.05 Branch)! 🛡️"
            echo "🤖 Qoder CLI:     $(qodercli --version 2>/dev/null || echo 'Ready')"
            echo "💡 Qoder UI:      Run 'qoder-desktop' to initiate the application client."
            echo "🗄️ Vector DB:     Run 'qdrant --storage-path ./.qdrant_storage' for storage."
            echo "🐍 Python:        $(python3 --version)"
            echo "🍞 Bun:           $(bun --version)"
            echo "🟢 Node (LTS):    $(node --version)"
            
            if [ ! -d ".venv" ]; then
              uv venv --python python3.13
            fi
            source .venv/bin/activate
          '';

          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc
            pkgs.zlib
            pkgs.openssl
            pkgs.glib
          ];
          NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
        };
      });
}
