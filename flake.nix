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
            inherit system overlays; config.allowUnfree = true;
          };
          vapourPlugins = with pkgs; [
            ffms
            vapoursynth-mvtools
            vapoursynthPlugins.vsutil
            vapoursynthPlugins.havsfunc
            vapoursynthPlugins.removegrain
          ];

          vapour = pkgs.vapoursynth.withPlugins vapourPlugins;
          vsedit = pkgs.vapoursynth-editor.withPlugins vapourPlugins;

          python = pkgs.python3.withPackages
            (ps: with ps; [
              multiprocess
              pymediainfo
              watchdog
            ]
            );
          svt-av1-psy = pkgs.callPackage ./pkgs/svt-av1-psy.nix { };
        in
        with pkgs;
        {
          devShells.default = mkShell {
            buildInputs = [
              opusTools
              libaom
              svt-av1-psy
              rav1e
              ffmpeg-full
              vapour
              (av1an.override {
                withAom = true;
                withSvtav1 = true;
                withVmaf = true;
                withRav1e = true;
                svt-av1 = svt-av1-psy;
                vapoursynth = vapour;
                av1an-unwrapped = pkgs.av1an-unwrapped.override {
                  vapoursynth = vapour;
                };
              })
              mediainfo
              python
              mkvtoolnix-cli
              ffms
              vsedit
            ];
          };
        }
      );
}
