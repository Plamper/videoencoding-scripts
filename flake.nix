{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    vs-overlay = {
      url = "github:nix-community/vs-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs = { self, nixpkgs, flake-utils, vs-overlay }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let
          overlays = [ (import vs-overlay) ];
          pkgs = import nixpkgs {
            inherit system overlays;
          };
          vapour = pkgs.vapoursynth.withPlugins [
            (pkgs.callPackage ./pkgs/vapoursynth-lsmash.nix { })
            pkgs.ffms
          ];

          python = pkgs.python3.withPackages
            (ps: with ps; [
              multiprocess
              pymediainfo
              watchdog
            ]
            );
          # svt-psy = pkgs.callPackage ./pkgs/svt-av1-psy.nix { };
          # libaom-psy101 = pkgs.callPackage ./pkgs/aom-psy101.nix { };
        in
        with pkgs;
        {
          devShells.default = mkShell {
            buildInputs = [
              opusTools
              libaom
              svt-av1
              rav1e
              ffmpeg-full
              vapour
              (av1an.override {
                withAom = true;
                withSvtav1 = true;
                withVmaf = true;
                withRav1e = true;
                # libaom = libaom-psy101;
                # svt-av1 = svt-psy;
                av1an-unwrapped = pkgs.av1an-unwrapped.override {
                  vapoursynth = vapour;
                #   libaom = libaom-psy101;
                };
              })
              mediainfo
              python
              mkvtoolnix-cli
              # libaom-psy101
              # svt-psy
            ];
          };
        }
      );
}
