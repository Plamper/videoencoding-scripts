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
            pkgs.ffms
          ];

          python = pkgs.python3.withPackages
            (ps: with ps; [
              multiprocess
              pymediainfo
              watchdog
            ]
            );
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
                av1an-unwrapped = pkgs.av1an-unwrapped.override {
                  vapoursynth = vapour;
                };
              })
              mediainfo
              python
              mkvtoolnix-cli
            ];
          };
        }
      );
}
