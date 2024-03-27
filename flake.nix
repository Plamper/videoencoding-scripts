{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    vs-overlay.url = "github:nix-community/vs-overlay";
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

          python= pkgs.python3.withPackages
            (ps: with ps; [
              multiprocess
              pymediainfo
            ]
            );
        in
        with pkgs;
        {
          devShells.default = mkShell {
            buildInputs = [
              opusTools
              libaom
              rav1e
              ffmpeg-full
              vapour
              (callPackage ./pkgs/av1an.nix { vapoursynth = vapour; })
              (callPackage ./pkgs/svt-av1-psy.nix { })
              mediainfo
              python
              mkvtoolnix-cli
            ];
          };
        }
      );
}
