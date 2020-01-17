#!/usr/bin/env sh
# Add license boilerplate to files.
if [ $# -lt 1 ]; then
  error "Missing boilerplate file"
else
  boilerplate=$1
  shift
fi
if [ $# -ge 1 ]; then
  files="$@"
else
  files=$(git ls-files)
fi

mfile="_relicense_.txt"
afile="_relicense_.awk"
cat <<EOF > $afile
@load "readfile"
BEGIN {
  notice = readfile("$boilerplate")
}
{
  if ( /\/\/ See [[:graph:]]+ for license details\./ && FNR==1 ) {
    print notice
  } else if ( /^[[:space:]]*$/ && FNR==2) {
  } else {
    print \$0
  }
}
EOF
for f in $files; do
  osize=$(stat -c %s $f)
  gawk -f $afile $f > $mfile
  msize=$(stat -c %s $mfile)
  if [ $msize -gt $osize ] && ! cmp -s $f $mfile; then
    mv $mfile $f
  fi
done
