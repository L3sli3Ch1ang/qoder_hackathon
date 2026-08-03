{
  description = "Stable Hackathon Stack: FastAPI + Bun React + Qoder CLI";

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

        # Native libraries the pip-installed binary wheels (numpy, torch,
        # sentence-transformers) dlopen at runtime. Exposed on LD_LIBRARY_PATH
        # so the standard dynamic linker used by the uv venv can find them.
        # Fixes: ImportError: libstdc++.so.6: cannot open shared object file.
        nativeLibs = with pkgs; [
          stdenv.cc.cc.lib   # libstdc++.so.6, libgcc_s.so.1
          gcc                # libgomp.so.1 (OpenMP)
          zlib               # libz.so.1
          openssl            # libssl.so, libcrypto.so
          glib               # libglib-2.0.so.0
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            # Latest stable Qoder CLI wrapper via Numtide
            llm-agents.packages.${system}.qoder-cli

            # Local Graphical IDEs (Accessible without root/system rebuilds)
            pkgs.jetbrains.webstorm
            pkgs.jetbrains.pycharm-oss

            # Frontend & Stable JavaScript Tooling
            pkgs.bun
            pkgs.nodejs_22 # Fixed: Changed from nodejs-22_x to nodejs_22

            pkgs.ffmpeg_7

            # Headless Chrome for HyperFrames/Puppeteer video rendering
            pkgs.chromium

            # Backend Core (Python 3.13 & uv build systems)
            pkgs.uv
            pkgs.python313

            # Database & Local Utility
            pkgs.sqlite
          ];

          shellHook = ''
            echo "🛡️ Stable Hackathon Environment Loaded! 🛡️"
            echo "🤖 Qoder CLI:  $(qodercli --version 2>/dev/null || echo 'Ready')"
            echo "🐍 Python:     $(python3 --version)"
            echo "🍞 Bun:        $(bun --version)"
            echo "🟢 Node (LTS): $(node --version)"
            
            # Setup local isolation for dependencies using uv
            if [ ! -d ".venv" ]; then
              uv venv --python python3.13
            fi
            source .venv/bin/activate
          '';

          # Standard loader path: lets the venv's C extensions (numpy/torch)
          # find libstdc++ & friends. This is the one that fixes the ImportError.
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath nativeLibs;

          # nix-ld path: for running arbitrary non-nix dynamically-linked binaries.
          NIX_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath nativeLibs;
          NIX_LD = pkgs.lib.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
        };
      });
}
