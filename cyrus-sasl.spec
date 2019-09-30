%global username    saslauth
%global hint        Saslauthd user
%global homedir     /run/saslauthd

%global bootstrap_cyrus_sasl 0

Name: cyrus-sasl
Version: 2.1.27
Release: 5
Summary: The Cyrus SASL API Implementation

License: BSD with advertising
URL: https://www.cyrusimap.org/sasl/
Source0: cyrus-sasl-%{version}-nodlcompatorsrp.tar.gz
Source5: saslauthd.service
Source7: sasl-mechlist.c
Source9: saslauthd.sysconfig
Source10: make-no-dlcompatorsrp-tarball.sh
Source11: autogen.sh

Patch11: cyrus-sasl-2.1.25-no_rpath.patch
Patch15: cyrus-sasl-2.1.20-saslauthd.conf-path.patch
Patch23: cyrus-sasl-2.1.23-man.patch
Patch24: cyrus-sasl-2.1.21-sizes.patch
Patch49: cyrus-sasl-2.1.26-md5global.patch
Patch6000: 0003-Prevent-double-free-of-RC4-context.patch

BuildRequires: autoconf, automake, libtool, gdbm-devel, groff
BuildRequires: krb5-devel >= 1.2.2, openssl-devel, pam-devel, pkgconfig
BuildRequires: mariadb-connector-c-devel, postgresql-devel, zlib-devel
BuildRequires: libdb-devel
%if ! %{bootstrap_cyrus_sasl}
BuildRequires: openldap-devel
%endif
%{?systemd_requires}

Requires(pre): /usr/sbin/useradd /usr/sbin/groupadd
Requires(postun): /usr/sbin/userdel /usr/sbin/groupdel
Requires: /sbin/nologin
Requires: systemd >= 211

Provides: user(%username)
Provides: group(%username)
Provides: %{name}-lib %{name}-lib%{?_isa}
Provides: %{name}-gssapi %{name}-gssapi%{?_isa}
Provides: %{name}-plain %{name}-md5 %{name}-ntlm
Provides: %{name}-sql %{name}-ldap %{name}-scram %{name}-gs2
Obsoletes: %{name}-lib %{name}-lib%{?_isa}
Obsoletes: %{name}-gssapi %{name}-gssapi%{?_isa}
Obsoletes: %{name}-plain %{name}-md5 %{name}-ntlm
Obsoletes: %{name}-sql %{name}-ldap %{name}-scram %{name}-gs2

%description
The %{name} package contains the Cyrus implementation of SASL.
SASL is the Simple Authentication and Security Layer, a method for
adding authentication support to connection-based protocols.

%package devel
Summary: Development files for %{name}
Requires: %{name} = %{version}-%{release}
Requires: pkgconf

%description devel
The %{name}-devel package contains files needed for developing and
compiling applications which use the Cyrus SASL library.

%package sql
Summary: SQL auxprop support for Cyrus SASL
Requires: %{name} = %{version}-%{release}

%description sql
The %{name}-sql package contains the Cyrus SASL plugin which supports
using a RDBMS for storing shared secrets.

%package_help

%prep
%autosetup -n %{name}-%{version} -p1

%build
cp %{SOURCE11} ./
rm configure aclocal.m4 config/ltmain.sh Makefile.in
export NOCONFIGURE=yes
sh autogen.sh
 
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
        --with-dblib=berkeley \
        --with-bdb=db \
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
 
pushd lib
../libtool --mode=link %{__cc} -o sasl2-shared-mechlist -I../include $CFLAGS %{SOURCE7} $LDFLAGS ./libsasl2.la
 

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
install -m644 -p saslauthd/testsaslauthd.8 $RPM_BUILD_ROOT%{_mandir}/man8/testsaslauthd.8
install -d -m755 $RPM_BUILD_ROOT/%{_unitdir} $RPM_BUILD_ROOT/etc/sysconfig
install -m644 -p %{SOURCE5} $RPM_BUILD_ROOT/%{_unitdir}/saslauthd.service
install -m644 -p %{SOURCE9} $RPM_BUILD_ROOT/etc/sysconfig/saslauthd
install -m755 -d $RPM_BUILD_ROOT/%{_sysconfdir}/sasl2
install -m755 -d $RPM_BUILD_ROOT/%{_libdir}/sasl2
 
./libtool --mode=install \
install -m755 lib/sasl2-shared-mechlist $RPM_BUILD_ROOT/%{_sbindir}/
 
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
%config(noreplace) /etc/sysconfig/saslauthd
%dir %{_sysconfdir}/sasl2
%{_sbindir}/pluginviewer
%{_sbindir}/saslauthd
%{_sbindir}/testsaslauthd
%{_sbindir}/saslpasswd2
%{_sbindir}/sasldblistusers2
%{_sbindir}/sasl2-shared-mechlist
%{_libdir}/libsasl*.so.*
%dir %{_libdir}/sasl2/
%{_libdir}/sasl2/*anonymous*.so*
%{_libdir}/sasl2/*sasldb*.so*
%{_libdir}/sasl2/*plain*.so*
%{_libdir}/sasl2/*login*.so*
%if ! %{bootstrap_cyrus_sasl}
%{_libdir}/sasl2/*ldapdb*.so*
%endif
%{_libdir}/sasl2/*crammd5*.so*
%{_libdir}/sasl2/*digestmd5*.so*
%{_libdir}/sasl2/*ntlm*.so*
%{_libdir}/sasl2/*gssapi*.so*
%{_libdir}/sasl2/libscram.so*
%{_libdir}/sasl2/libgs2.so*
%{_unitdir}/saslauthd.service
%ghost /run/saslauthd

%files devel
%defattr(-,root,root)
%{_bindir}/sasl2-sample-client
%{_bindir}/sasl2-sample-server
%{_includedir}/*
%{_libdir}/libsasl*.*so
%{_libdir}/pkgconfig/*.pc

%files sql
%defattr(-,root,root)
%{_libdir}/sasl2/*sql*.so*

%files help
%defattr(-,root,root)
%doc doc/html/*.html saslauthd/LDAP_SASLAUTHD
%{_mandir}/man3/*
%{_mandir}/man8/*


%changelog
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
