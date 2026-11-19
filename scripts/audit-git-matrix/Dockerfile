# One git release built from its kernel.org source tarball, on Python 3.12, for running
# the audit tool's acceptance suite against that git. Distribution packages backport
# security fixes, so only a source build gives the exact release.
#
# Build: docker build --build-arg GIT_VERSION=2.41.0 -t audit-git-matrix:2.41.0 \
#          scripts/audit-git-matrix
# The suite runs as an unprivileged user, so that its unreadable-directory cases hold.
FROM python:3.12-slim

ARG GIT_VERSION
RUN test -n "${GIT_VERSION}" \
 && apt-get update \
 && apt-get install -y --no-install-recommends build-essential zlib1g-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN curl -fsSLO "https://www.kernel.org/pub/software/scm/git/git-${GIT_VERSION}.tar.gz" \
 && curl -fsSLO "https://www.kernel.org/pub/software/scm/git/sha256sums.asc" \
 && grep " git-${GIT_VERSION}.tar.gz\$" sha256sums.asc | sha256sum -c - \
 && tar -xzf "git-${GIT_VERSION}.tar.gz" \
 && make -C "git-${GIT_VERSION}" -j"$(nproc)" \
      CFLAGS="-O2 -w -std=gnu17 -fpermissive" \
      NO_CURL=1 NO_EXPAT=1 NO_TCLTK=1 NO_GETTEXT=1 NO_PERL=1 NO_PYTHON=1 NO_OPENSSL=1 \
      prefix=/opt/git install \
 && rm -rf /build

ENV PATH=/opt/git/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home auditor
USER auditor
WORKDIR /home/auditor
