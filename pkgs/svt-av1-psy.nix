{ lib
, stdenv
, fetchFromGitHub
, cmake
, nasm
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "svt-av1-psy";
  version = "2.2.1";

  src = fetchFromGitHub {
    owner = "gianni-rosato";
    repo = "svt-av1-psy";
    rev = "v${finalAttrs.version}";
    hash = "sha256-4ds7yrUMp0O5/aWOkdnrANR1D3djajU/0ZeY6xJnpHI=";
  };

  patches = [ ./cmakelists.patch ];

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
    homepage = "https://gitlab.com/AOMediaCodec/SVT-AV1";
    description = "AV1-compliant encoder/decoder library core";

    longDescription = ''
      The Scalable Video Technology for AV1 (SVT-AV1 Encoder and Decoder) is an
      AV1-compliant encoder/decoder library core. The SVT-AV1 encoder
      development is a work-in-progress targeting performance levels applicable
      to both VOD and Live encoding / transcoding video applications. The
      SVT-AV1 decoder implementation is targeting future codec research
      activities.
    '';

    changelog = "https://gitlab.com/AOMediaCodec/SVT-AV1/-/blob/v${finalAttrs.version}/CHANGELOG.md";
    license = with licenses; [ aom bsd3 ];
    maintainers = with maintainers; [ Madouura ];
    platforms = platforms.unix;
  };
})
