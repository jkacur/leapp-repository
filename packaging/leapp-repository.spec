%global leapp_datadir %{_datadir}/leapp-repository
%global repositorydir %{leapp_datadir}/repositories
%global custom_repositorydir %{leapp_datadir}/custom-repositories
# Defining py_byte_compile macro because it is not defined in old rpm (el7)
# Only defined to python2 since python3 is not used in RHEL7
%{!?py_byte_compile: %global py_byte_compile py2_byte_compile() {\
    python_binary="%1"\
    bytecode_compilation_path="%2"\
    find $bytecode_compilation_path -type f -a -name "*.py" -print0 | xargs -0 $python_binary -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("$RPM_BUILD_ROOT")[2]) for f in sys.argv[1:]]' || :\
    find $bytecode_compilation_path -type f -a -name "*.py" -print0 | xargs -0 $python_binary -O -c 'import py_compile, sys; [py_compile.compile(f, dfile=f.partition("$RPM_BUILD_ROOT")[2]) for f in sys.argv[1:]]' || :\
}\
py2_byte_compile "%1" "%2"}


Name:           leapp-repository
Version:        0.11.0
Release:        1%{?dist}
Summary:        Repositories for leapp

License:        ASL 2.0
URL:            https://oamg.github.io/leapp/
Source0:        https://github.com/oamg/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        deps-pkgs.tar.gz
BuildArch:      noarch
BuildRequires:  python-devel

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Provides in deps subpackage
Requires:       leapp-repository-dependencies = 5

# IMPORTANT: this is capability provided by the leapp framework rpm.
# Check that 'version' this instead of the real framework rpm version.
Requires:       leapp-framework >= 1.3, leapp-framework < 2
Requires:       python2-leapp

# That's temporary to ensure the obsoleted subpackage is not installed
# and will be removed when the current version of leapp-repository is installed
Obsoletes:      leapp-repository-data <= 0.6.1
Provides:       leapp-repository-data <= 0.6.1

# Former leapp subpackage that was packacking a leapp sos plugin - the plugin
# is part of the sos package since RHEL 7.8
Obsoletes:      leapp-repository-sos-plugin <= 0.9.0

%description
Repositories for leapp


# This metapackage should contain all RPM dependencies exluding deps on *leapp*
# RPMs. This metapackage will be automatically replaced during the upgrade
# to satisfy dependencies with RPMs from target system.
%package deps
Summary:    Meta-package with system dependencies of %{name} package

# IMPORTANT: everytime the requirements are changed, increment number by one
# - same for Requires in main package
Provides:  leapp-repository-dependencies = 5
##################################################
# Real requirements for the leapp-repository HERE
##################################################
Requires:   dnf >= 4
Requires:   pciutils
%if 0%{?rhel} && 0%{?rhel} == 7
# Required to gather system facts about SELinux
Requires:   libselinux-python
Requires:   python-pyudev
# required by SELinux actors
Requires:   policycoreutils-python
%else ## RHEL 8 dependencies ##
# Requires:   systemd-container
%endif
##################################################
# end requirement
##################################################


%description deps
%{summary}


%prep
%autosetup -n %{name}-%{version}
%setup -q  -n %{name}-%{version} -D -T -a 1


%build
# ??? what is supposed to be this? we do not have any build target in the makefile
make build
cp -a leapp*deps*rpm repos/system_upgrade/el7toel8/files/bundled-rpms/


%install
install -m 0755 -d %{buildroot}%{custom_repositorydir}
install -m 0755 -d %{buildroot}%{repositorydir}
cp -r repos/* %{buildroot}%{repositorydir}/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/repos.d/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/transaction/
install -m 0755 -d %{buildroot}%{_sysconfdir}/leapp/files/
install -m 0644 etc/leapp/transaction/* %{buildroot}%{_sysconfdir}/leapp/transaction

# Remove irrelevant repositories - We don't want to ship them
rm -rf %{buildroot}%{repositorydir}/containerization
rm -rf %{buildroot}%{repositorydir}/test

# remove component/unit tests, Makefiles, ... stuff that related to testing only
rm -rf %{buildroot}%{repositorydir}/common/actors/testactor
find %{buildroot}%{repositorydir}/common -name "test.py" -delete
rm -rf `find %{buildroot}%{repositorydir} -name "tests" -type d`
find %{buildroot}%{repositorydir} -name "Makefile" -delete

for DIRECTORY in $(find  %{buildroot}%{repositorydir}/  -mindepth 1 -maxdepth 1 -type d);
do
    REPOSITORY=$(basename $DIRECTORY)
    echo "Enabling repository $REPOSITORY"
    ln -s  %{repositorydir}/$REPOSITORY  %{buildroot}%{_sysconfdir}/leapp/repos.d/$REPOSITORY
done;

%py_byte_compile %{__python} %{buildroot}%{repositorydir}/*


%files
%doc README.md
%license LICENSE
%dir %{_sysconfdir}/leapp/transaction
%dir %{_sysconfdir}/leapp/files
%dir %{leapp_datadir}
%dir %{repositorydir}
%dir %{custom_repositorydir}
%{_sysconfdir}/leapp/repos.d/*
%{_sysconfdir}/leapp/transaction/*
%{repositorydir}/*


%files deps
# no files here


# DO NOT TOUCH SECTION BELOW IN UPSTREAM
%changelog
* Mon Apr 16 2018 Vinzenz Feenstra <evilissimo@redhat.com> - %{version}-%{release}
- Initial RPM
