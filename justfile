set dotenv-load

default:
    @just --list

# ---------- setup ----------
[group('setup')]
@install:
    uv sync

[group('setup')]
@lock:
    uv lock --upgrade

[group('setup')]
@update_all: lock update_alpine update_icons
    uv sync --all-extras --upgrade
    uvx --with pre-commit-uv prek auto-update

[group('setup')]
@update *args:
    uv sync --upgrade-package {{ args }}

[group('setup')]
update_alpine:
    #!/usr/bin/env bash
    set -euo pipefail
    STATIC_DIR="static/js"
    VERSION_FILE="static/js/.alpine-version"

    LATEST=$(curl -sf https://registry.npmjs.org/alpinejs/latest \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")

    CURRENT=""
    if [ -f "$VERSION_FILE" ]; then
        CURRENT=$(cat "$VERSION_FILE")
    fi

    if [ "$CURRENT" = "$LATEST" ]; then
        echo "✓ Alpine $LATEST already up to date"
        exit 0
    fi

    echo "⬇️  Updating Alpine: ${CURRENT:-none} → $LATEST"

    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    fetch() {  # $1 = npm package, $2 = destination filename
        TARBALL=$(curl -sf "https://registry.npmjs.org/$1/latest" \
            | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['tarball'])")
        DEST="$TMP_DIR/$2"
        mkdir -p "$DEST"
        curl -sf "$TARBALL" | tar -xz -C "$DEST"
        cp "$DEST/package/dist/cdn.min.js" "$STATIC_DIR/$2"
    }

    mkdir -p "$STATIC_DIR"
    fetch alpinejs alpine.min.js
    fetch @alpinejs/collapse alpine-collapse.min.js
    fetch @alpinejs/focus alpine-focus.min.js

    echo "$LATEST" > "$VERSION_FILE"
    echo "✓ Alpine $LATEST installed in $STATIC_DIR"

# The handful of Phosphor icons the admin wears, vendored like Alpine: they are
# masks painted with the text colour, so only the outline matters. The bold
# weight, because at 14px the regular one goes thin beside the text. MIT licence.
[group('setup')]
update_icons:
    #!/usr/bin/env bash
    set -euo pipefail
    STATIC_DIR="static/img/icons"
    VERSION_FILE="$STATIC_DIR/.phosphor-version"
    ICONS=(plus pencil-simple trash eye eye-slash calendar-blank clock)
    WEIGHT="bold"

    LATEST=$(curl -sf https://registry.npmjs.org/@phosphor-icons/core/latest \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])")

    CURRENT=""
    if [ -f "$VERSION_FILE" ]; then
        CURRENT=$(cat "$VERSION_FILE")
    fi

    MISSING=""
    for icon in "${ICONS[@]}"; do
        [ -f "$STATIC_DIR/$icon.svg" ] || MISSING="yes"
    done

    # The weight is part of the stamp, so changing it re-fetches on its own.
    if [ "$CURRENT" = "$LATEST $WEIGHT" ] && [ -z "$MISSING" ]; then
        echo "✓ Phosphor $LATEST already up to date"
        exit 0
    fi

    echo "⬇️  Updating Phosphor: ${CURRENT:-none} → $LATEST $WEIGHT"

    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    TARBALL=$(curl -sf "https://registry.npmjs.org/@phosphor-icons/core/latest" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['dist']['tarball'])")
    curl -sf "$TARBALL" | tar -xz -C "$TMP_DIR"

    mkdir -p "$STATIC_DIR"
    for icon in "${ICONS[@]}"; do
        # Saved under the plain name: the weight is this recipe's business,
        # not something the stylesheet has to know about.
        cp "$TMP_DIR/package/assets/$WEIGHT/$icon-$WEIGHT.svg" "$STATIC_DIR/$icon.svg"
    done

    echo "$LATEST $WEIGHT" > "$VERSION_FILE"
    echo "✓ Phosphor $LATEST ($WEIGHT): ${ICONS[*]} in $STATIC_DIR"

# ---------- development ----------
[group('development')]
@local:
    uv run python manage.py tailwind runserver

[group('development')]
@serve:
    mprocs -c mprocs-local.yaml

# The mail pane of `just serve`. Wrapped only so a missing binary says why the
# pane went away; installing it is the developer's call, not this recipe's.
_mailpit:
    #!/usr/bin/env bash
    if ! command -v mailpit > /dev/null; then
        echo "WARNING: mailpit is not installed, so nothing catches the mail sent"
        echo "in development and every send fails. Install it with: brew install mailpit"
        exit 0
    fi
    exec mailpit

[group('development')]
migrate:
    uv run python manage.py migrate

[group('development')]
makemigrations *args:
    uv run python manage.py makemigrations {{ args }}

# Example association, form and events, so a fresh clone has a full home page.
[group('development')]
seed_demo:
    uv run python manage.py seed_demo

[group('development')]
crawl *args:
    uv run python manage.py crawl -v 2 {{ args }}

[group('development')]
messages:
    uv run python manage.py makemessages -l it -l en --ignore=.venv
    uv run python manage.py compilemessages -l it -l en --ignore=.venv

# ---------- tests ----------
[group('utility')]
test *args:
    ENVIRONMENT=test uv run python -m pytest --reuse-db -s -x {{ args }}

[group('utility')]
ftest *args:
    nice -n 10 taskpolicy -b env ENVIRONMENT=test uv run pytest -n ${TEST_WORKERS:-4} \
        --reuse-db --dist loadscope --exitfirst {{ args }}

[group('utility')]
cov *args:
    nice -n 10 taskpolicy -b env ENVIRONMENT=test uv run pytest -n ${TEST_WORKERS:-4} \
        --reuse-db --dist loadscope --exitfirst --cov=. \
        --cov-report html:htmlcov --cov-report term:skip-covered \
        --cov-fail-under 100 {{ args }}

# ---------- quality ----------
[group('utility')]
lint:
    nice -n 10 just _pre-commit run --all-files

[group('utility')]
check:
    ENVIRONMENT=prod DEBUG=False uv run python manage.py check --deploy

_pre-commit *args:
    uvx prek {{ args }}
