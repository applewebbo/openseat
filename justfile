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
    uvx --with pre-commit-uv prek update

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

# They are masks painted with the text colour, so only the outline matters. The
# bold weight, because at 14px the regular one goes thin beside the text. MIT.
# Vendor the handful of Phosphor icons the admin wears, the way Alpine is
[group('setup')]
update_icons:
    #!/usr/bin/env bash
    set -euo pipefail
    STATIC_DIR="static/img/icons"
    VERSION_FILE="$STATIC_DIR/.phosphor-version"
    ICONS=(plus pencil-simple trash eye eye-slash calendar-blank clock user armchair check download-simple)
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

# The province/comuni pair for the address selects: ISTAT's own "Elenco dei
# comuni italiani", under IODL 2.0 — vendored once, refreshed by hand, never
# fetched live from a page visitor's browser.
[group('setup')]
update_comuni:
    #!/usr/bin/env bash
    set -euo pipefail
    DATA_DIR="intake/data"
    SOURCE="https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv"
    TMP_CSV=$(mktemp)
    trap "rm -f $TMP_CSV" EXIT

    curl -sfL --retry 3 "$SOURCE" -o "$TMP_CSV"

    mkdir -p "$DATA_DIR"
    uv run python3 - "$TMP_CSV" "$DATA_DIR/comuni.json" <<'PY'
    import csv
    import json
    import sys
    from collections import defaultdict

    source, destination = sys.argv[1], sys.argv[2]
    province = {}
    comuni = defaultdict(set)

    with open(source, encoding="latin-1") as f:
        for row in csv.DictReader(f, delimiter=";"):
            sigla = (row.get("Sigla automobilistica") or "").strip()
            nome_provincia = (
                row.get(
                    "Denominazione dell'Unità territoriale sovracomunale \n"
                    "(valida a fini statistici)"
                )
                or ""
            ).strip()
            nome_comune = (row.get("Denominazione in italiano") or "").strip()
            if not sigla or not nome_comune:
                continue
            province[sigla] = nome_provincia
            comuni[sigla].add(nome_comune)

    data = {
        "province": sorted(
            ({"sigla": s, "nome": n} for s, n in province.items()),
            key=lambda p: p["sigla"],
        ),
        "comuni": {sigla: sorted(names) for sigla, names in comuni.items()},
    }
    with open(destination, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")

    print(f"✓ {len(data['province'])} province, {sum(len(v) for v in data['comuni'].values())} comuni")
    PY

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

# ---------- github ----------
# origin may point elsewhere, so every gh call names the repository
github_repo := "applewebbo/openseat"

[group('github')]
issues state="open":
    gh issue list -R {{ github_repo }} --state {{ state }}

[group('github')]
issue number:
    #!/usr/bin/env bash
    set -euo pipefail
    gh issue view {{ number }} -R {{ github_repo }}
    comments=$(gh issue view {{ number }} -R {{ github_repo }} --comments)
    if [ -n "$comments" ]; then
        printf '\n--- Comments ---\n%s\n' "$comments"
    fi

[group('github')]
issue-create title body="":
    gh issue create -R {{ github_repo }} --title "{{ title }}" --body "{{ body }}"

[group('github')]
issue-comment number file:
    gh issue comment {{ number }} -R {{ github_repo }} --body-file {{ file }}

[group('github')]
issue-edit-body number file:
    gh issue edit {{ number }} -R {{ github_repo }} --body-file {{ file }}

[group('github')]
issue-close number:
    gh issue close {{ number }} -R {{ github_repo }}

[group('github')]
issue-reopen number:
    gh issue reopen {{ number }} -R {{ github_repo }}

# --force updates the colour when the label is already there
[group('github')]
label-create name color="0E8A16":
    gh label create "{{ name }}" -R {{ github_repo }} --color "{{ color }}" --force

[group('github')]
issue-label number *labels:
    #!/usr/bin/env bash
    set -euo pipefail
    for label in {{ labels }}; do
        gh issue edit {{ number }} -R {{ github_repo }} --add-label "$label"
        echo "✓ label '$label' added to issue #{{ number }}"
    done

[group('github')]
release-list:
    gh release list -R {{ github_repo }}

[group('github')]
release-show tag:
    gh release view "{{ tag }}" -R {{ github_repo }}

# Push main and the tag, then cut the release
[group('github')]
release-create tag previous_tag="" notes_file="" draft="false" prerelease="false":
    #!/usr/bin/env bash
    set -euo pipefail

    git push origin main

    if git rev-parse "{{ tag }}" >/dev/null 2>&1; then
        echo "tag {{ tag }} already exists"
    else
        git tag "{{ tag }}"
    fi
    git push origin "refs/tags/{{ tag }}"

    if [ -n "{{ notes_file }}" ]; then
        NOTES_FILE="{{ notes_file }}"
    else
        NOTES_FILE=$(mktemp /tmp/release-notes-XXXXXX.md)
        if [ -n "{{ previous_tag }}" ]; then
            PREV_TAG="{{ previous_tag }}"
        else
            PREV_TAG=$(git tag --sort=-version:refname | grep -v "{{ tag }}" | head -1)
        fi
        COMMITS=$(git log ${PREV_TAG}..{{ tag }} --pretty=format:"- %s" --reverse 2>/dev/null || echo "- Initial release")
        {
            echo "## What's New in {{ tag }}"
            echo ""
            for section in "feat:### ✨ Features" "fix:### 🐛 Bug Fixes" \
                           "chore|build|ci:### 🛠️ Maintenance" "test:### 🚨 Tests" \
                           "docs:### 📚 Documentation" "refactor|style:### ♻️ Refactoring"; do
                pattern=${section%%:*}
                heading=${section#*:}
                body=$(echo "$COMMITS" | grep -E "^- (${pattern})" || true)
                if [ -n "$body" ]; then
                    printf '%s\n%s\n\n' "$heading" "$body"
                fi
            done
            echo "### 📖 Full Changelog"
            echo "https://github.com/{{ github_repo }}/compare/${PREV_TAG}...{{ tag }}"
        } > "$NOTES_FILE"
    fi

    RELEASE_FLAGS=(--title "{{ tag }}" --notes-file "$NOTES_FILE")
    if [ "{{ draft }}" = "true" ]; then
        RELEASE_FLAGS+=(--draft)
    fi
    if [ "{{ prerelease }}" = "true" ]; then
        RELEASE_FLAGS+=(--prerelease)
    fi

    gh release create "{{ tag }}" -R {{ github_repo }} "${RELEASE_FLAGS[@]}"

# ---------- housekeeping ----------
# Removes the Tailwind binary too: the next build downloads ~120MB again
[group('setup')]
clean:
    rm -rf .venv .pytest_cache .ruff_cache .coverage htmlcov .django_tailwind_cli
    find . -type d -name "__pycache__" -exec rm -r {} +

[group('setup')]
fresh: clean install
