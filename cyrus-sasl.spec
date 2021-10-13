%global username    saslauth
%global hint        Saslauthd user
%global homedir     /run/saslauthd

%global bootstrap_cyrus_sasl 0

Name: cyrus-sasl
Version: 2.1.27
Release: 13
Summary: The Cyrus SASL API Implementation

License: BSD with advertising
URL: https://www.cyrusimap.org/sasl/
Source0: https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-2.1.27/cyrus-sasl-2.1.27.tar.gz
Source1: saslauthd.service
Source2: saslauthd.sysconfig

Patch0: 0003-Prevent-double-free-of-RC4-context.patch
Patch1: fix-CVE-2019-19906.patch
Patch2: backport-db_gdbm-fix-gdbm_errno-overlay-from-gdbm_close.patch

BuildRequires: autoconf, automake, libtool, gdbm-devel, groff
BuildRequires: krb5-devel >= 1.2.2, openssl-devel, pam-devel, pkgconfig
BuildRequires: mariadb-connector-c-devel, postgresql-devel, zlib-devel

%{?systemd_requires}

Requires(pre): /usr/sbin/useradd /usr/sbin/groupadd
Requires(postun): /usr/sbin/userdel /usr/sbin/groupdel
Requires: /sbin/nologin
Requires: systemd >= 211

Provides: user(%username)
Provides: group(%username)

%description
The %{name} package contains the Cyrus implementation of SASL.
SASL is the Simple Authentication and Security Layer, a method for
adding authentication support to connection-based protocols.

%package devel
Summary: Development files for %{name}
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: pkgconf

%description devel
The %{name}-devel package contains files needed for developing and
compiling applications which use the Cyrus SASL library.

%if ! %{bootstrap_cyrus_sasl}

%package ldap
BuildRequires: openldap-devel
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: LDAP auxprop support for Cyrus SASL

%description ldap
The %{name}-ldap package contains the Cyrus SASL plugin which supports using
a directory server, accessed using LDAP, for storing shared secrets.

%endif

%package gssapi
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: GSSAPI authentication support for Cyrus SASL

%description gssapi
The %{name}-gssapi package contains the Cyrus SASL plugins which
support GSSAPI authentication. GSSAPI is commonly used for Kerberos
authentication.

%package plain
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: PLAIN and LOGIN authentication support for Cyrus SASL

%description plain
The %{name}-plain package contains the Cyrus SASL plugins which support
PLAIN and LOGIN authentication schemes.

%package md5
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: CRAM-MD5 and DIGEST-MD5 authentication support for Cyrus SASL

%description md5
The %{name}-md5 package contains the Cyrus SASL plugins which support
CRAM-MD5 and DIGEST-MD5 authentication schemes.

%package ntlm
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: NTLM authentication support for Cyrus SASL

%description ntlm
The %{name}-ntlm package contains the Cyrus SASL plugin which supports
the NTLM authentication scheme.

%package scram
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: SCRAM auxprop support for Cyrus SASL

%description scram
The %{name}-scram package contains the Cyrus SASL plugin which supports
the SCRAM authentication scheme.

%package gs2
Requires: %{name}-lib%{?_isa} = %{version}-%{release}
Conflicts: %{name} < 2.1.27-13
Summary: GS2 support for Cyrus SASL

%description gs2
The %{name}-gs2 package contains the Cyrus SASL plugin which supports
the GS2 authentication scheme.

%package lib
Summary: Shared libraries needed by applications which use Cyrus SASL

%description lib
The %{name}-lib package contains shared libraries which are needed by
applications which use the Cyrus SASL library.

%package sql
Summary: SQL auxprop support for Cyrus SASL
Requires: %{name}-lib%{?_isa} = %{version}-%{release}

%description sql
The %{name}-sql package contains the Cyrus SASL plugin which supports
using a RDBMS for storing shared secrets.

%package_help

%prep
%autosetup -n %{name}-%{version} -p1

%build
rm configure aclocal.m4 config/ltmain.sh Makefile.in
export NOCONFIGURE=yes
aclocal --install
autoreconf --verbose --force --install -Wno-portability
 
krb5_prefix=`krb5-config --prefix`
if test x$krb5_prefix = x%{_prefix} ; then
        krb5_prefix=
else
        CPPFLAGS="-I${krb5_prefix}/include $CPPFLAGS"; export CPPFLAGS
        LDFLAGS="-L${krb5_prefix}/%{_lib} $LDFLAGS"; export LDFLAGS
fi
 
LIBS="-lcrypt"; export LIBS
if pkg-config openssl ; then
        CPPFLAGS="`pkg-config --cflags-only-I openssl` $CPPFLAGS"; export CPPFLAGS
        LDFLAGS="`pkg-config --libs-only-L openssl` $LDFLAGS"; export LDFLAGS
fi
 
INC_DIR="`mysql_config --include`"
if test x"$INC_DIR" != "x-I%{_includedir}"; then
        CPPFLAGS="$INC_DIR $CPPFLAGS"; export CPPFLAGS
fi
LIB_DIR="`mysql_config --libs | sed -e 's,-[^L][^ ]*,,g' -e 's,^ *,,' -e 's, *$,,' -e 's,  *, ,g'`"
if test x"$LIB_DIR" != "x-L%{_libdir}"; then
        LDFLAGS="$LIB_DIR $LDFLAGS"; export LDFLAGS
fi
 
INC_DIR="-I`pg_config --includedir`"
if test x"$INC_DIR" != "x-I%{_includedir}"; then
        CPPFLAGS="$INC_DIR $CPPFLAGS"; export CPPFLAGS
fi
LIB_DIR="-L`pg_config --libdir`"
if test x"$LIB_DIR" != "x-L%{_libdir}"; then
        LDFLAGS="$LIB_DIR $LDFLAGS"; export LDFLAGS
fi
 
CFLAGS="$RPM_OPT_FLAGS $CFLAGS $CPPFLAGS -fPIC -pie -Wl,-z,relro -Wl,-z,now"; export CFLAGS
 
echo "$CFLAGS"
echo "$CPPFLAGS"
echo "$LDFLAGS"
 
%configure \
        --enable-shared --disable-static \
        --disable-java \
        --with-plugindir=%{_libdir}/sasl2 \
        --with-configdir=%{_libdir}/sasl2:%{_sysconfdir}/sasl2 \
        --disable-krb4 \
        --enable-gssapi${krb5_prefix:+=${krb5_prefix}} \
        --with-gss_impl=mit \
        --with-rc4 \
        --with-bdb=gdbm \
        --with-saslauthd=/run/saslauthd --without-pwcheck \
%if ! %{bootstrap_cyrus_sasl}
        --with-ldap \
%endif
        --with-devrandom=/dev/urandom \
        --enable-anon \
        --enable-cram \
        --enable-digest \
        --enable-ntlm \
        --enable-plain \
        --enable-login \
        --enable-alwaystrue \
        --enable-httpform \
        --disable-otp \
%if ! %{bootstrap_cyrus_sasl}
        --enable-ldapdb \
%endif
        --enable-sql --with-mysql=yes --with-pgsql=yes \
        --without-sqlite \
        "$@"
make sasldir=%{_libdir}/sasl2
make -C saslauthd testsaslauthd
make -C sample
 

%install
test "$RPM_BUILD_ROOT" != "/" && rm -rf $RPM_BUILD_ROOT
 
make install DESTDIR=$RPM_BUILD_ROOT sasldir=%{_libdir}/sasl2
make install DESTDIR=$RPM_BUILD_ROOT sasldir=%{_libdir}/sasl2 -C plugins
 
install -m755 -d $RPM_BUILD_ROOT%{_bindir}
./libtool --mode=install \
install -m755 sample/client $RPM_BUILD_ROOT%{_bindir}/sasl2-sample-client
./libtool --mode=install \
install -m755 sample/server $RPM_BUILD_ROOT%{_bindir}/sasl2-sample-server
./libtool --mode=install \
install -m755 saslauthd/testsaslauthd $RPM_BUILD_ROOT%{_sbindir}/testsaslauthd
install -m755 -d $RPM_BUILD_ROOT%{_mandir}/man8/
install -m644 -p saslauthd/saslauthd.mdoc $RPM_BUILD_ROOT%{_mandir}/man8/saslauthd.8
install -m755 -d $RPM_BUILD_ROOT/etc/rc.d/init.d $RPM_BUILD_ROOT/etc/sysconfig
install -d -m755 $RPM_BUILD_ROOT/%{_unitdir}
install -m644 -p %{SOURCE1} $RPM_BUILD_ROOT/%{_unitdir}/saslauthd.service
install -m644 -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/saslauthd
install -m755 -d $RPM_BUILD_ROOT/%{_sysconfdir}/sasl2
install -m755 -d $RPM_BUILD_ROOT/%{_libdir}/sasl2
 
rm -f $RPM_BUILD_ROOT%{_libdir}/sasl2/libotp.*
rm -f $RPM_BUILD_ROOT%{_mandir}/cat8/saslauthd.8
%delete_la_and_a

%check
make check

%pre
getent group %{username} >/dev/null || groupadd -g 76 -r %{username}
getent passwd %{username} >/dev/null || useradd -r -g %{username} -d %{homedir} -s /sbin/nologin -c "%{hint}" %{username}

%post
%systemd_post saslauthd.service

%preun
%systemd_preun saslauthd.service

%postun
%systemd_postun_with_restart saslauthd.service

%files
%defattr(-,root,root)
%license COPYING
%doc AUTHORS
%dir %{_sysconfdir}/sasl2
%{_sbindir}/pluginviewer
%{_sbindir}/saslauthd
%{_sbindir}/testsaslauthd
%config(noreplace) /etc/sysconfig/saslauthd
%{_unitdir}/saslauthd.service
%ghost /run/saslauthd

%files lib
%{_libdir}/libsasl*.so.*
%dir %{_sysconfdir}/sasl2
%{_libdir}/libsasl*.so.*
%dir %{_libdir}/sasl2/
%{_libdir}/sasl2/*anonymous*.so*
%{_libdir}/sasl2/*sasldb*.so*
%{_sbindir}/saslpasswd2
%{_sbindir}/sasldblistusers2

%files devel
%defattr(-,root,root)
%{_bindir}/sasl2-sample-client
%{_bindir}/sasl2-sample-server
%{_includedir}/*
%{_libdir}/libsasl*.*so
%{_libdir}/pkgconfig/*.pc

%if ! %{bootstrap_cyrus_sasl}
%files ldap
%{_libdir}/sasl2/*ldapdb*.so*
%endif

%files sql
%defattr(-,root,root)
%{_libdir}/sasl2/*sql*.so*

%files plain
%{_libdir}/sasl2/*plain*.so*
%{_libdir}/sasl2/*login*.so*

%files md5
%{_libdir}/sasl2/*crammd5*.so*
%{_libdir}/sasl2/*digestmd5*.so*

%files ntlm
%{_libdir}/sasl2/*ntlm*.so*

%files gssapi
%{_libdir}/sasl2/*gssapi*.so*

%files scram
%{_libdir}/sasl2/libscram.so*

%files gs2
%{_libdir}/sasl2/libgs2.so*

%files help
%defattr(-,root,root)
%doc doc/html/*.html saslauthd/LDAP_SASLAUTHD
%{_mandir}/man3/*
%{_mandir}/man8/*


%changelog
* Wed Oct 13 2021 liyanan <liyanan32@huawei.com> - 2.1.27-13
- Split cyrus-sasl-ldap cyrus-sasl-gs2 cyrus-sasl-scram cyrus-sasl-gssapi
  cyrus-sasl-md5 cyrus-sasl-ntlm cyrus-sasl-plain sub-package

* Wed May 12 2021 wangchen <wangchen137@huawei.com> - 2.1.27-12
- fix gdbm_errno overlay from gdbm_close

* Fri Jan 8 2021 yangzhuangzhuang <yangzhuangzhuang1@huawei.com> - 2.1.27-11
- BuildRequires: replace libdb with gdbm

* Sat Mar 21 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-10
- add missing saslauthd.sysconfig for saslauthd.service

* Tue Mar 10 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-9
- fix CVE-2019-19906

* Mon Feb 17 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-8
- add cyrus-sasl-lib containing dynamic library for cyrus-sasl

* Tue Jan 7 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-7
- simplify functions

* Mon Dec 23 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-6
- Fix update problem

* Tue Sep 24 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-5
- Require adjust

* Mon Sep 23 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-4
- Add cyrus-sasl-sql package

* Mon Sep 23 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-3
- Fix libpq dependency problems

* Mon Sep 23 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-2
- Fix cyrus-sasl-gssapi dependency problems

* Thu Sep 19 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.1.27-1
- Package init
