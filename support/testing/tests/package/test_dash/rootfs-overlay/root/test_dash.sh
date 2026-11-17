#! /bin/dash
#
# Simple POSIX shell script exercising some dash features.
# Each check prints "FAIL: ..." and exits with a non-zero code on
# error, or prints "PASS" at the end on success.

fail() {
	echo "FAIL: $*"
	exit 1
}

# Arithmetic expansion
[ "$((6 * 7))" -eq 42 ] || fail "arithmetic"

# Parameter expansion
VAR="buildroot-dash.tar.gz"
[ "${VAR%%.*}" = "buildroot-dash" ] || fail "suffix removal"
[ "${VAR#*-}" = "dash.tar.gz" ] || fail "prefix removal"
[ "${#VAR}" -eq 21 ] || fail "string length"
[ "${UNSET_VAR:-default}" = "default" ] || fail "default value"

# Functions, local variables and return codes
f() {
	local x
	x="$1"
	return "$x"
}
f 3
[ $? -eq 3 ] || fail "function return code"

# Loops and case
sum=0
for i in 1 2 3 4 5; do
	sum=$((sum + i))
done
[ "$sum" -eq 15 ] || fail "for loop"

n=0
while [ "$n" -lt 10 ]; do
	n=$((n + 1))
done
[ "$n" -eq 10 ] || fail "while loop"

case "$VAR" in
	*.tar.gz) ;;
	*) fail "case pattern" ;;
esac

# Command substitution and pipelines
[ "$(echo hello | tr '[:lower:]' '[:upper:]')" = "HELLO" ] || fail "pipeline"

# Here-document
out=$(cat <<HEREDOC
value=$sum
HEREDOC
)
[ "$out" = "value=15" ] || fail "here-document"

# Subshell does not leak variables
SUB=outer
# shellcheck disable=SC2030,SC2031
(SUB=inner)
# shellcheck disable=SC2031
[ "$SUB" = "outer" ] || fail "subshell"

# Traps
tmp=$(mktemp)
(trap 'echo trapped > '"$tmp" EXIT; exit 0)
[ "$(cat "$tmp")" = "trapped" ] || fail "trap on exit"
rm -f "$tmp"

# set -e behavior: "false" must abort the subshell, so "true" is
# never reached and the subshell exit code is non-zero. Note that the
# subshell can't be used directly in an "if" condition, as "set -e" is
# ignored in that context.
(set -e; false; true)
ret=$?
[ "$ret" -ne 0 ] || fail "set -e"

echo "PASS"
