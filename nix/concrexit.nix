{ stdenv
, poetry2nix
, file
, uwsgi
, pkgs
, writeScript
, src
, version ? "git"
}:
let
  concrexit-env = poetry2nix.mkPoetryEnv {
    projectDir = src;
    # The overrides we do here are patches copied from nixpkgs, some patches are also included
    # in poetry2nix but for Pillow they don't work well enough and python-magic isn't included
    overrides = poetry2nix.overrides.withDefaults (
      self: super: {
        pillow = super.pillow.overridePythonAttrs (
          old: with pkgs; {
            preConfigure =
              let
                libinclude' = pkg: ''"${pkg.out}/lib", "${pkg.out}/include"'';
                libinclude = pkg: ''"${pkg.out}/lib", "${pkg.dev}/include"'';
              in
              ''
                sed -i "setup.py" \
                    -e 's|^FREETYPE_ROOT =.*$|FREETYPE_ROOT = ${libinclude freetype}|g ;
                        s|^JPEG_ROOT =.*$|JPEG_ROOT = ${libinclude libjpeg}|g ;
                        s|^JPEG2K_ROOT =.*$|JPEG2K_ROOT = ${libinclude openjpeg}|g ;
                        s|^IMAGEQUANT_ROOT =.*$|IMAGEQUANT_ROOT = ${libinclude' libimagequant}|g ;
                        s|^ZLIB_ROOT =.*$|ZLIB_ROOT = ${libinclude zlib}|g ;
                        s|^LCMS_ROOT =.*$|LCMS_ROOT = ${libinclude lcms2}|g ;
                        s|^TIFF_ROOT =.*$|TIFF_ROOT = ${libinclude libtiff}|g ;
                        s|^TCL_ROOT=.*$|TCL_ROOT = ${libinclude' tcl}|g ;
                        s|self\.disable_platform_guessing = None|self.disable_platform_guessing = True|g ;'
                export LDFLAGS="-L${libwebp}/lib"
                export CFLAGS="-I${libwebp}/include"
              ''
              # Remove impurities
              + stdenv.lib.optionalString stdenv.isDarwin ''
                substituteInPlace setup.py \
                  --replace '"/Library/Frameworks",' "" \
                  --replace '"/System/Library/Frameworks"' ""
              '';
            nativeBuildInputs = [ pkgconfig ] ++ old.nativeBuildInputs;
            propagatedBuildInputs = [ self.olefile ];
            buildInputs = [ freetype libjpeg openjpeg zlib libtiff libwebp tcl lcms2 ] ++ old.buildInputs;
          }
        );
        python-magic = super.python-magic.overridePythonAttrs (_old: {
          postPatch = ''
            substituteInPlace magic.py --replace "ctypes.util.find_library('magic')" "'${file}/lib/libmagic${stdenv.hostPlatform.extensions.sharedLibrary}'"
          '';
        });
        # We don't install uswgi from pypi but instead use the nixpkgs version
        uwsgi = { };
      }
    );
  };

  # Location of the manage.py script
  manage-py = "${src}/website/manage.py";

  # We want to enable the python3 plugin for uwsgi, so we override here
  uwsgi-python = uwsgi.override { plugins = [ "python3" ]; python3 = concrexit-env; };

  # Wrapper script that sets the right options for uWSGI
  concrexit-uwsgi = writeScript "concrexit-uwsgi" ''
    MANAGE_PY=1 ${concrexit-env}/bin/python ${manage-py} migrate

    ${uwsgi-python}/bin/uwsgi $@ \
      --plugins python3 \
      --socket-timeout 1800 \
      --threads 5 \
      --processes 5 \
      --pythonpath ${concrexit-env}/${concrexit-env.sitePackages} \
      --chdir ${src}/website \
      --module thaliawebsite.wsgi:application \
      --log-master \
      --harakiri 1800 \
      --max-requests 5000 \
      --vacuum \
      --limit-post 0 \
      --post-buffering 16384 \
      --thunder-lock \
      --ignore-sigpipe \
      --ignore-write-errors \
      --disable-write-exception
  '';

in
stdenv.mkDerivation {
  pname = "concrexit";
  inherit version src;

  buildInputs = [ concrexit-env file ];

  # Build all static files beforehand
  buildPhase = ''
    export STATIC_ROOT=static
    export DJANGO_ENV=production

    MANAGE_PY=1 python website/manage.py collectstatic
    MANAGE_PY=1 python website/manage.py compress
  '';

  doCheck = true;

  checkPhase = ''
    export DJANGO_ENV=development
    python website/manage.py check
    python website/manage.py templatecheck --project-only
    python website/manage.py makemigrations --no-input --check --dry-run
    python website/manage.py test website/
  '';

  # Place the static files and the python env in the right location
  installPhase = ''
    mkdir --parents $out/bin

    cp ${concrexit-uwsgi} $out/bin/concrexit-uwsgi

    cp -r ${concrexit-env}/* $out
    cp -r static $out
    ln -s ${src} $out/src
  '';

  # So we can access the environment for shell.nix
  passthru = {
    env = concrexit-env;
  };
}
