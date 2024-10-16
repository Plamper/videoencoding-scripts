{ lib
, stdenv
, fetchFromGitHub
, cmake
, nasm
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "svt-av1-psy";
  version = "2.2.1-B";

  src = fetchFromGitHub {
    owner = "gianni-rosato";
    repo = "svt-av1-psy";
    rev = "v${finalAttrs.version}";
    hash = "sha256-3GF60XMKglpU82S5XNyW1DBYtU0KVrfghRVYokZTGoI=";
  };

  nativeBuildInputs = [
    cmake
    nasm
  ];

  cmakeFlags = [
    "-DSVT_AV1_LTO=ON"
    "-DCMAKE_CXX_FLAGS=-O3"
    "-DCMAKE_C_FLAGS=-O3"
    "-DCMAKE_LD_FLAGS=-O3"
    "-DCMAKE_BUILD_TYPE=Release"
    "-DBUILD_DEC=OFF"
    "-DNATIVE=ON"
  ];


  meta = with lib; {
    homepage = "https://github.com/gianni-rosato/svt-av1-psy";
    description = "AV1-compliant encoder/decoder library core";

    longDescription = ''
      SVT-AV1-PSY is the Scalable Video Technology for AV1 (SVT-AV1 
      Encoder and Decoder) with perceptual enhancements for 
      psychovisually optimal AV1 encoding. The goal is to create 
      the best encoding implementation for perceptual quality with AV1.
    '';

    changelog = "https://github.com/gianni-rosato/svt-av1-psy/blob/v${finalAttrs.version}/CHANGELOG.md";
    license = with licenses; [ aom bsd3 ];
    platforms = platforms.unix;
  };
})
