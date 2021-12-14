{ stdenv
, poetry2nix
, file
, uwsgi
, ghostscript
, pkgs
, lib
, runCommand
, python38
, writeScriptBin
, version ? "git"
}:
let
  concrexit-python = python38;

  src = ./.;

  poetryPython = poetry2nix.mkPoetryPackages {
    projectDir = src;
    overrides = poetry2nix.overrides.withDefaults (
      _self: super: {
        python-magic = concrexit-python.pkgs.python_magic;
        cryptography = super.cryptography.overridePythonAttrs (old: {
          cargoDeps = pkgs.rustPlatform.fetchCargoTarball {
            inherit (old) src;
            name = "${old.pname}-${old.version}";
            sourceRoot = "${old.pname}-${old.version}/src/rust/";
            sha256 = "sha256-tQoQfo+TAoqAea86YFxyj/LNQCiViu5ij/3wj7ZnYLI=";
          };
          cargoRoot = "src/rust";
          buildInputs = old.buildInputs ++ [ pkgs.libiconv ];
          nativeBuildInputs = old.nativeBuildInputs ++ (with pkgs.rustPlatform; [
            rust.rustc
            rust.cargo
            cargoSetupHook
          ]);
        });
      }
    );
    python = concrexit-python;
  };

  inherit (poetryPython) poetryPackages pyProject;

  concrexit-env = poetryPython.python.buildEnv.override { extraLibs = poetryPackages; };

  # We want to enable the python3 plugin for uwsgi, so we override here
  uwsgi-python = (uwsgi.override { plugins = [ "python3" ]; python3 = concrexit-python; }).overrideAttrs (old: { buildInputs = old.buildInputs ++ [ pkgs.zlib pkgs.expat ]; });

  # Wrapper script that sets the right options for uWSGI
  concrexit-uwsgi = writeScriptBin "concrexit-uwsgi" ''
    #! ${pkgs.runtimeShell}
    cd ${concrexit}/website
    MANAGE_PY=1 ${concrexit-env}/bin/python ${concrexit}/website/manage.py migrate

    ${uwsgi-python}/bin/uwsgi "$@" \
      --plugins python3 \
      --socket-timeout 1800 \
      --threads 5 \
      --processes 5 \
      --pythonpath ${concrexit-env}/${concrexit-env.sitePackages} \
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
      --disable-write-exception \
      --stats /tmp/uwsgi-stats.socket
  '';

  concrexit = stdenv.mkDerivation {
    pname = moduleName pyProject.tool.poetry.name;
    version = pyProject.tool.poetry.version;
    inherit src;

    buildInputs = [ concrexit-env ];

    # Build all static files beforehand
    buildPhase = ''
      export STATIC_ROOT=static
      export DJANGO_ENV=production

      MANAGE_PY=1 python website/manage.py collectstatic
      MANAGE_PY=1 python website/manage.py compress
    '';

    # doCheck = true;

    # checkPhase = ''
    #   export DJANGO_ENV=development
    #   python website/manage.py check
    #   python website/manage.py templatecheck --project-only
    #   python website/manage.py makemigrations --no-input --check --dry-run
    #   python website/manage.py test website/
    # '';

    # Place the static files and the python env in the right location
    installPhase = ''
      mkdir $out

      cp -r website $out/website
      cp -r static $out/static
    '';
  };

  # Do some canonicalisation of module names
  moduleName = name: lib.toLower (lib.replaceStrings [ "_" "." ] [ "-" "-" ] name);

in
pkgs.buildEnv {
  name = moduleName pyProject.tool.poetry.name + "-" + pyProject.tool.poetry.version;

  paths = [
    concrexit-env
    uwsgi-python
    concrexit
    concrexit-uwsgi
    ghostscript
    file
  ];
}
