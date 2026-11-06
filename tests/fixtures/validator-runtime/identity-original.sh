test_public_identity_matches_exact_ledger_and_preserves_knowledge() (
  local root scratch files ledger_file ledger_heading ledger_title ledger_suffix baseline_commit
  local path_field line_field token_field path lines token count line_number file input
  local row candidate_count=0 row_count=0 expected_count=0 identity_prefix identity_join identity_suffix identity_pattern
  local content token_entry matches status
  local -A token_counts=()
  root="$(pwd -P)" || return 1
  scratch="$(mktemp -d "${TMPDIR:-/tmp}/identity-scan.XXXXXX")" || return 1
  trap 'rm -rf "$scratch"' EXIT

  # Assemble the scan term so the validator never stores the complete former name.
  identity_prefix='agentic'
  identity_join='[_-]'
  identity_suffix='workflows'
  identity_pattern="${identity_prefix}${identity_join}${identity_suffix}"

  git ls-files --cached --others --exclude-standard -z > "$scratch/all-files" || return 1
  : > "$scratch/scan-files" || return 1

  # The one state record carrying the ledger is discovered by its unique heading.
  # Split the heading fragments so this source cannot discover itself as the ledger.
  ledger_title='Exact Identity'
  ledger_suffix='Match Ledger'
  ledger_heading="### ${ledger_title} ${ledger_suffix}"
  while IFS= read -r -d '' candidate; do
    if [ -f "$root/$candidate" ] && grep -Fq "$ledger_heading" "$root/$candidate"; then
      ledger_file="$candidate"
      candidate_count=$((candidate_count + 1))
    fi
  done < "$scratch/all-files"
  [ "$candidate_count" -eq 1 ] || {
    echo 'Expected exactly one identity match ledger'; return 1;
  }

  # Scan all repository files. Mask only the markdown table rows beneath the
  # discovered ledger heading; its heading and surrounding prose remain scanned.
  while IFS= read -r -d '' file; do
    printf '%s\0' "$file" >> "$scratch/scan-files" || return 1
  done < "$scratch/all-files"

  awk -F'|' -v start="$ledger_heading" '
    function valid_row() {
      return NF == 5 && substr($0, 1, 1) == "|" && substr($0, length($0), 1) == "|" &&
        $1 ~ /^[[:space:]]*$/ && $5 ~ /^[[:space:]]*$/ &&
        $2 ~ /^[[:space:]]*`[^`]+`[[:space:]]*$/ &&
        $3 ~ /^[[:space:]]*[0-9]+(,[[:space:]]*[0-9]+)*[[:space:]]*$/ &&
        $4 ~ /^[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?([[:space:]]*;[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?)*[[:space:]]*$/
    }
    $0 == start { in_ledger = 1; next }
    in_ledger && /^### / { in_ledger = 0 }
    in_ledger && /^\|/ {
      if ($0 == "| Path | Line | Expected token counts |" || $0 == "|---|---:|---|") next
      if (valid_row()) { print; found = 1; next }
      invalid = 1
    }
    END { if (!found || invalid) exit 1 }
  ' "$ledger_file" > "$scratch/ledger-rows" || {
    echo 'Identity ledger has no exact path rows'; return 1;
  }

  : > "$scratch/expected" || return 1
  while IFS= read -r row; do
    IFS='|' read -r _ path_field line_field token_field _ <<< "$row"
    path="$(sed -E 's/^[[:space:]]*`([^`]*)`.*/\1/' <<< "$path_field")" || return 1
    lines="$(tr -d '[:space:]' <<< "$line_field")" || return 1
    case "$path" in
      ''|/*|../*|*/../*) echo 'Identity ledger contains an invalid path'; return 1 ;;
    esac
    [ -n "$lines" ] && [ -n "$token_field" ] || {
      echo 'Identity ledger contains an incomplete row'; return 1;
    }
    printf '%s\0' "$path" >> "$scratch/scan-files" || return 1
    row_count=$((row_count + 1))

    IFS=',' read -r -a line_entries <<< "$lines"
    IFS=';' read -r -a token_entries <<< "$token_field"
    [ "${#line_entries[@]}" -gt 0 ] && [ "${#token_entries[@]}" -gt 0 ] || return 1
    for line_number in "${line_entries[@]}"; do
      [[ "$line_number" =~ ^[0-9]+$ ]] || {
        echo 'Identity ledger contains an invalid line number'; return 1;
      }
      for token_entry in "${token_entries[@]}"; do
        token="$(sed -nE 's/.*`([^`]*)`.*/\1/p' <<< "$token_entry")" || return 1
        count="$(sed -nE 's/.*×[[:space:]]*([0-9]+).*/\1/p' <<< "$token_entry")" || return 1
        [[ -n "$token" && "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]] || {
          echo 'Identity ledger contains an invalid token count'; return 1;
        }
        printf '%s\t%s\t%s\t%s\n' "$path" "$line_number" "$token" "$count" >> "$scratch/expected" || return 1
        expected_count=$((expected_count + 1))
      done
    done
  done < "$scratch/ledger-rows"
  [ "$row_count" -gt 0 ] && [ "$expected_count" -gt 0 ] || return 1

  sort -zu "$scratch/scan-files" -o "$scratch/scan-files" || return 1
  : > "$scratch/actual" || return 1
  while IFS= read -r -d '' file; do
    if [ -L "$root/$file" ]; then
      readlink -- "$root/$file" > "$scratch/link" || {
        printf 'Cannot read scanned symlink: %s\n' "$file"; return 1;
      }
      input="$scratch/link"
    elif [ -f "$root/$file" ] && [ -r "$root/$file" ]; then
      input="$root/$file"
    else
      printf 'Scanned path is missing or unreadable: %s\n' "$file"; return 1
    fi

    if [ "$file" = "$ledger_file" ]; then
      awk -F'|' -v start="$ledger_heading" '
        function valid_row() {
          return NF == 5 && substr($0, 1, 1) == "|" && substr($0, length($0), 1) == "|" &&
            $1 ~ /^[[:space:]]*$/ && $5 ~ /^[[:space:]]*$/ &&
            $2 ~ /^[[:space:]]*`[^`]+`[[:space:]]*$/ &&
            $3 ~ /^[[:space:]]*[0-9]+(,[[:space:]]*[0-9]+)*[[:space:]]*$/ &&
            $4 ~ /^[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?([[:space:]]*;[[:space:]]*`[^`]+`[[:space:]]*×[[:space:]]*[0-9]+([[:space:]]+per line)?)*[[:space:]]*$/
        }
        $0 == start { in_ledger = 1; print; next }
        in_ledger && /^### / { in_ledger = 0 }
        in_ledger && valid_row() { print ""; next }
        { print }
      ' "$input" > "$scratch/ledger-source-scan" || return 1
      input="$scratch/ledger-source-scan"
    fi

    line_number=0
    while IFS= read -r content || [ -n "$content" ]; do
      line_number=$((line_number + 1))
      token_counts=()
      status=0
      matches="$(printf '%s\n' "$content" | grep -aEio "$identity_pattern")" || status=$?
      case "$status" in
        0)
          while IFS= read -r token; do
            token_counts["$token"]=$(( ${token_counts["$token"]:-0} + 1 ))
          done <<< "$matches"
          for token in "${!token_counts[@]}"; do
            printf '%s\t%s\t%s\t%s\n' "$file" "$line_number" "$token" "${token_counts[$token]}" >> "$scratch/actual" || return 1
          done
          ;;
        1) ;;
        *) printf 'Identity scan failed on %s:%s\n' "$file" "$line_number"; return 1 ;;
      esac
    done < "$input"
  done < "$scratch/scan-files"

  LC_ALL=C sort "$scratch/expected" -o "$scratch/expected" || return 1
  LC_ALL=C sort "$scratch/actual" -o "$scratch/actual" || return 1
  if ! diff -u "$scratch/expected" "$scratch/actual" > "$scratch/diff"; then
    echo 'Identity scan differs from the exact path, line, token, and count ledger:'
    sed -n '1,80p' "$scratch/diff"
    return 1
  fi

  # The recorded base commit defines the knowledge inventory before this change.
  baseline_commit="$(awk '/^  base_commit:/ { value = $2; found = 1 } END { if (found) print value }' "$ledger_file")"
  [[ "$baseline_commit" =~ ^[[:xdigit:]]{40}$ ]] || {
    echo 'Identity ledger state has no valid baseline commit'; return 1;
  }
  git cat-file -e "${baseline_commit}^{commit}" 2>/dev/null || {
    echo 'Identity ledger baseline commit is unavailable'; return 1;
  }
  git ls-tree -r --name-only "$baseline_commit" -- .ai > "$scratch/baseline" || return 1
  while IFS= read -r file; do
    [ -n "$file" ] || continue
    if [ ! -e "$file" ]; then
      case "$file" in
        .ai/tasks/todo/*) file=".ai/tasks/completed/${file#.ai/tasks/todo/}" ;;
        .ai/specs/*) file=".ai/specs/completed/${file#.ai/specs/}" ;;
      esac
    fi
    [ -e "$file" ] || { printf 'Knowledge file was removed: %s\n' "$file"; return 1; }
    git ls-files --error-unmatch -- "$file" >/dev/null 2>&1 || {
      printf 'Knowledge file is no longer tracked: %s\n' "$file"; return 1;
    }
  done < "$scratch/baseline"
)
