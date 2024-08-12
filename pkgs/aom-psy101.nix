{ lib
, stdenv
, fetchFromGitLab
, yasm
, perl
, cmake
, pkg-config
, python3
}:

let
  isCross = stdenv.buildPlatform != stdenv.hostPlatform;
in
stdenv.mkDerivation rec {
  pname = "libaom";
  version = "3.9.0";

  src = fetchFromGitLab {
    owner = "damian101";
    repo = "aom-psy101";
    rev = "psy101";
    hash = "sha256-fC1sk1mWy4yUGtZuGN6Bj1BCpOIKfZChsHJsqJ3Rfvs=";
  };

  patches = [ ./outputs.patch ];

  nativeBuildInputs = [
    yasm
    perl
    cmake
    pkg-config
    python3
  ];

  preConfigure = ''
    # build uses `git describe` to set the build version
    cat > $NIX_BUILD_TOP/git << "EOF"
    #!${stdenv.shell}
    echo v${version}
    EOF
    chmod +x $NIX_BUILD_TOP/git
    export PATH=$NIX_BUILD_TOP:$PATH
  '';

  # Configuration options:
  # https://aomedia.googlesource.com/aom/+/refs/heads/master/build/cmake/aom_config_defaults.cmake

  cmakeFlags = [
    "-DBUILD_SHARED_LIBS=ON"
    "-DENABLE_DOCS=0"
    "-DCONFIG_TUNE_BUTTERAUGLI=0"
    "-DCONFIG_TUNE_VMAF=0"
    "-DCONFIG_AV1_DECODER=0"
    "-DENABLE_TESTS=0"
    "-DCMAKE_BUILD_TYPE=Release"
  ];

  postFixup = ''
    moveToOutput lib/libaom.a "$static"
  '' + lib.optionalString stdenv.hostPlatform.isStatic ''
    ln -s $static $out
  '';

  outputs = [ "out" "bin" "dev" "static" ];

}
