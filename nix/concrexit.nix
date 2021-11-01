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
      _self: super: {
        pillow = pkgs.python3.pkgs.pillow;
        python-magic = pkgs.python3.pkgs.python_magic;
        # We don't install uswgi from pypi but instead use the nixpkgs version
        uwsgi = { };
        # TODO: change when https://github.com/nix-community/poetry2nix/issues/413 is fixed
        cryptography = super.cryptography.overridePythonAttrs (old: {
          cargoDeps = pkgs.rustPlatform.fetchCargoTarball {
            inherit (old) src;
            name = "${old.pname}-${old.version}";
            sourceRoot = "${old.pname}-${old.version}/src/rust/";
            sha256 = "sha256-tQoQfo+TAoqAea86YFxyj/LNQCiViu5ij/3wj7ZnYLI=";
          };
          cargoRoot = "src/rust";
          nativeBuildInputs = old.nativeBuildInputs ++ (with pkgs.rustPlatform; [
            rust.rustc
            rust.cargo
            cargoSetupHook
          ]);
        });
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
