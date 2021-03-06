#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# RPM spec file for Traffic Ops (tm).
#

%define TRAFFIC_OPS_USER trafops
%define TRAFFIC_OPS_GROUP trafops
%define TRAFFIC_OPS_LOG_DIR /var/log/traffic_ops

Summary:          Traffic Ops UI
Name:             traffic_ops
Version:          %{traffic_control_version}
Release:          %{build_number}
License:          Apache License, Version 2.0
Group:            Base System/System Tools
Prefix:           /opt/traffic_ops
Source:           %{_sourcedir}/traffic_ops-%{version}.tgz
URL:              https://github.com/apache/incubator-trafficcontrol/
Vendor:           Apache Software Foundation
Packager:         daniel_kirkwood at Cable dot Comcast dot com
AutoReqProv:      no
Requires:         cpanminus, expat-devel, gcc-c++, libcurl, libpcap-devel, mkisofs, tar
Requires:         openssl-devel, perl, perl-core, perl-DBD-Pg, perl-DBI, perl-Digest-SHA1
Requires:         libidn-devel, libcurl-devel, libcap
Requires:         postgresql96 >= 9.6.2 , postgresql96-devel >= 9.6.2
Requires:         perl-JSON, perl-libwww-perl, perl-Test-CPAN-Meta, perl-WWW-Curl, perl-TermReadKey, perl-Crypt-ScryptKDF
Requires(pre):    /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel

%define PACKAGEDIR %{prefix}

%description
Installs Traffic Ops.

Built: %(date) by %{getenv: USER}

%prep

%setup

%build
    # update version referenced in the source
    perl -pi.bak -e 's/__VERSION__/%{version}-%{release}/' app/lib/UI/Utils.pm

    export PATH=$PATH:/usr/local/go/bin
    export GOPATH=$(pwd)

    echo "PATH: $PATH"
    echo "GOPATH: $GOPATH"
    go version
    go env
    
    # Create build area with proper gopath structure
    mkdir -p src pkg bin || { echo "Could not create directories in $(pwd): $!"; exit 1; }

    # build tocookie (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/traffic_ops/tocookie
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/traffic_ops/tocookie/* . && \
      echo "go getting tocookie at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go tocookie at $(pwd): $!"; exit 1; }

    # build log (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/lib/go-log
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/lib/go-log/* . && \
      echo "go getting log at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go log at $(pwd): $!"; exit 1; }

    # build tc (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/lib/go-tc
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/lib/go-tc/* . && \
      echo "go getting tc at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go tc at $(pwd): $!"; exit 1; }

    # build util (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/lib/go-util
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/lib/go-util/* . && \
      echo "go getting util at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go util at $(pwd): $!"; exit 1; }

    # build TO client (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/traffic_ops/client
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/traffic_ops/client/* . && \
      echo "go getting log at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go Traffic Ops client at $(pwd): $!"; exit 1; }

    # build TO structs (dependencies within traffic_control will fail to `go get` unless prebuilt)
    godir=src/github.com/apache/incubator-trafficcontrol/traffic_ops/tostructs
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/traffic_ops/tostructs/* . && \
      echo "go getting log at $(pwd)" && \
      go get -v \
    ) || { echo "Could not build go Traffic Ops tostructs at $(pwd): $!"; exit 1; }



    # build traffic_ops_golang binary
    godir=src/github.com/apache/incubator-trafficcontrol/traffic_ops/traffic_ops_golang
    oldpwd=$(pwd)
    ( mkdir -p "$godir" && \
      cd "$godir" && \
      cp -r "$TC_DIR"/traffic_ops/traffic_ops_golang/* . && \
      echo "go getting at $(pwd)" && \
      go get -d -v && \
      echo "go building at $(pwd)" && \
      go build -ldflags "-B 0x`git rev-parse HEAD`" \
    ) || { echo "Could not build go program at $(pwd): $!"; exit 1; }

%install

    if [ -d $RPM_BUILD_ROOT ]; then
		%__rm -rf $RPM_BUILD_ROOT
    fi

    if [ ! -d $RPM_BUILD_ROOT/%{PACKAGEDIR} ]; then
		%__mkdir -p $RPM_BUILD_ROOT/%{PACKAGEDIR}
    fi

    %__cp -R $RPM_BUILD_DIR/traffic_ops-%{version}/* $RPM_BUILD_ROOT/%{PACKAGEDIR}
    echo "go rming $RPM_BUILD_ROOT/%{PACKAGEDIR}/{pkg,src,bin}"
    %__rm -rf $RPM_BUILD_ROOT/%{PACKAGEDIR}/{pkg,src,bin}

    %__mkdir -p $RPM_BUILD_ROOT/var/www/files
    %__cp install/data/perl/osversions.cfg $RPM_BUILD_ROOT/var/www/files/.

    if [ ! -d $RPM_BUILD_ROOT/%{PACKAGEDIR}/app/public/routing ]; then
        %__mkdir -p $RPM_BUILD_ROOT/%{PACKAGEDIR}/app/public/routing
    fi

    # install traffic_ops_golang binary
    if [ ! -d $RPM_BUILD_ROOT/%{PACKAGEDIR}/app/bin ]; then
        %__mkdir -p $RPM_BUILD_ROOT/%{PACKAGEDIR}/app/bin
    fi

    src=src/github.com/apache/incubator-trafficcontrol/traffic_ops/traffic_ops_golang
    %__cp -p  "$src"/traffic_ops_golang        "${RPM_BUILD_ROOT}"/opt/traffic_ops/app/bin/traffic_ops_golang
%pre
    /usr/bin/getent group %{TRAFFIC_OPS_GROUP} || /usr/sbin/groupadd -r %{TRAFFIC_OPS_GROUP}
    /usr/bin/getent passwd %{TRAFFIC_OPS_USER} || /usr/sbin/useradd -r -d %{PACKAGEDIR} -s /sbin/nologin %{TRAFFIC_OPS_USER} -g %{TRAFFIC_OPS_GROUP}
    if [ -d %{PACKAGEDIR}/app/conf ]; then
	  echo -e "\nBacking up config files.\n"
	  if [ -f /var/tmp/traffic_ops-backup.tar ]; then
		  %__rm /var/tmp/traffic_ops-backup.tar
	  fi
	  cd %{PACKAGEDIR} && tar cf /var/tmp/traffic_ops-backup.tar app/public/routing  app/conf app/db/dbconf.yml app/local app/cpanfile.snapshot
    fi

    # upgrade
    if [ "$1" == "2" ]; then
	systemctl stop traffic_ops
    fi

%post
    %__cp %{PACKAGEDIR}/etc/init.d/traffic_ops /etc/init.d/traffic_ops
    %__mkdir -p /var/www/files
    %__cp %{PACKAGEDIR}/etc/cron.d/trafops_dnssec_refresh /etc/cron.d/trafops_dnssec_refresh
    %__cp %{PACKAGEDIR}/etc/cron.d/trafops_clean_isos /etc/cron.d/trafops_clean_isos
    %__cp %{PACKAGEDIR}/etc/logrotate.d/traffic_ops /etc/logrotate.d/traffic_ops
    %__cp %{PACKAGEDIR}/etc/logrotate.d/traffic_ops_golang /etc/logrotate.d/traffic_ops_golang
    %__cp %{PACKAGEDIR}/etc/logrotate.d/traffic_ops_access /etc/logrotate.d/traffic_ops_access
    %__cp %{PACKAGEDIR}/etc/logrotate.d/traffic_ops_perl_access /etc/logrotate.d/traffic_ops_perl_access
    %__cp %{PACKAGEDIR}/etc/profile.d/traffic_ops.sh /etc/profile.d/traffic_ops.sh
    %__chown root:root /etc/init.d/traffic_ops
    %__chown root:root /etc/cron.d/trafops_dnssec_refresh
    %__chown root:root /etc/cron.d/trafops_clean_isos
    %__chown root:root /etc/logrotate.d/traffic_ops
    %__chown root:root /etc/logrotate.d/traffic_ops_golang
    %__chown root:root /etc/logrotate.d/traffic_ops_access
    %__chown root:root /etc/logrotate.d/traffic_ops_perl_access
    %__chmod +x /etc/init.d/traffic_ops
    %__chmod +x %{PACKAGEDIR}/install/bin/*
    /sbin/chkconfig --add traffic_ops
	
    %__mkdir -p %{TRAFFIC_OPS_LOG_DIR}

    if [ -f /var/tmp/traffic_ops-backup.tar ]; then
    	echo -e "\nRestoring config files.\n"
		cd %{PACKAGEDIR} && tar xf /var/tmp/traffic_ops-backup.tar
    fi

    # install
    if [ "$1" = "1" ]; then
      # see postinstall, the .reconfigure file triggers init().
    	echo -e "\nRun /opt/traffic_ops/install/bin/postinstall from the root home directory to complete the install.\n"
    fi

    # upgrade
    if [ "$1" == "2" ]; then
        echo -e "\n\nTo complete the update, perform the following steps:\n"
        echo -e "1. If any *.rpmnew files are in /opt/traffic_ops/...,  reconcile with any local changes\n"
        echo -e "2. Run 'PERL5LIB=/opt/traffic_ops/app/lib:/opt/traffic_ops/app/local/lib/perl5 ./db/admin.pl --env production upgrade'\n"
        echo -e "   from the /opt/traffic_ops/app directory.\n"
        echo -e "To start Traffic Ops:  systemctl start traffic_ops\n";
        echo -e "To stop Traffic Ops:   systemctl stop traffic_ops\n\n";
    fi
    /bin/chown -R %{TRAFFIC_OPS_USER}:%{TRAFFIC_OPS_GROUP} %{PACKAGEDIR}
    /bin/chown -R %{TRAFFIC_OPS_USER}:%{TRAFFIC_OPS_GROUP} %{TRAFFIC_OPS_LOG_DIR}
    setcap cap_net_bind_service=+ep %{PACKAGEDIR}/app/bin/traffic_ops_golang

%preun

if [ "$1" = "0" ]; then
    # stop service before starting the uninstall
    systemctl stop traffic_ops
fi

%postun

if [ "$1" = "0" ]; then
	# this is an uninstall
	%__rm -rf %{PACKAGEDIR}
	%__rm /etc/init.d/traffic_ops
    /usr/bin/getent passwd %{TRAFFIC_OPS_USER} || /usr/sbin/userdel %{TRAFFIC_OPS_USER} 
    /usr/bin/getent group %{TRAFFIC_OPS_GROUP} || /usr/sbin/groupdel %{TRAFFIC_OPS_GROUP}
fi

%files
%defattr(644,root,root,755)
%attr(755,root,root) %{PACKAGEDIR}/app/bin/*
%attr(755,root,root) %{PACKAGEDIR}/app/script/*
%attr(755,root,root) %{PACKAGEDIR}/app/db/*.pl
%config(noreplace)/opt/traffic_ops/app/conf/*
%config(noreplace)/var/www/files/osversions.cfg
%{PACKAGEDIR}/app/cpanfile
%{PACKAGEDIR}/app/db
%{PACKAGEDIR}/app/lib
%{PACKAGEDIR}/app/public
%{PACKAGEDIR}/app/templates
%{PACKAGEDIR}/install
%{PACKAGEDIR}/etc
%doc %{PACKAGEDIR}/doc
