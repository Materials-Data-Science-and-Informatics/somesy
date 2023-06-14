"""Core models for the somesy package."""
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic import AnyUrl, BaseModel, Extra, Field
from typing_extensions import Annotated


class LicenseEnum(Enum):
    """SPDX license identifiers."""

    field_0BSD = "0BSD"
    AAL = "AAL"
    Abstyles = "Abstyles"
    Adobe_2006 = "Adobe-2006"
    Adobe_Glyph = "Adobe-Glyph"
    ADSL = "ADSL"
    AFL_1_1 = "AFL-1.1"
    AFL_1_2 = "AFL-1.2"
    AFL_2_0 = "AFL-2.0"
    AFL_2_1 = "AFL-2.1"
    AFL_3_0 = "AFL-3.0"
    Afmparse = "Afmparse"
    AGPL_1_0 = "AGPL-1.0"
    AGPL_1_0_only = "AGPL-1.0-only"
    AGPL_1_0_or_later = "AGPL-1.0-or-later"
    AGPL_3_0 = "AGPL-3.0"
    AGPL_3_0_only = "AGPL-3.0-only"
    AGPL_3_0_or_later = "AGPL-3.0-or-later"
    Aladdin = "Aladdin"
    AMDPLPA = "AMDPLPA"
    AML = "AML"
    AMPAS = "AMPAS"
    ANTLR_PD = "ANTLR-PD"
    ANTLR_PD_fallback = "ANTLR-PD-fallback"
    Apache_1_0 = "Apache-1.0"
    Apache_1_1 = "Apache-1.1"
    Apache_2_0 = "Apache-2.0"
    APAFML = "APAFML"
    APL_1_0 = "APL-1.0"
    APSL_1_0 = "APSL-1.0"
    APSL_1_1 = "APSL-1.1"
    APSL_1_2 = "APSL-1.2"
    APSL_2_0 = "APSL-2.0"
    Artistic_1_0 = "Artistic-1.0"
    Artistic_1_0_cl8 = "Artistic-1.0-cl8"
    Artistic_1_0_Perl = "Artistic-1.0-Perl"
    Artistic_2_0 = "Artistic-2.0"
    Bahyph = "Bahyph"
    Barr = "Barr"
    Beerware = "Beerware"
    BitTorrent_1_0 = "BitTorrent-1.0"
    BitTorrent_1_1 = "BitTorrent-1.1"
    blessing = "blessing"
    BlueOak_1_0_0 = "BlueOak-1.0.0"
    Borceux = "Borceux"
    BSD_1_Clause = "BSD-1-Clause"
    BSD_2_Clause = "BSD-2-Clause"
    BSD_2_Clause_FreeBSD = "BSD-2-Clause-FreeBSD"
    BSD_2_Clause_NetBSD = "BSD-2-Clause-NetBSD"
    BSD_2_Clause_Patent = "BSD-2-Clause-Patent"
    BSD_2_Clause_Views = "BSD-2-Clause-Views"
    BSD_3_Clause = "BSD-3-Clause"
    BSD_3_Clause_Attribution = "BSD-3-Clause-Attribution"
    BSD_3_Clause_Clear = "BSD-3-Clause-Clear"
    BSD_3_Clause_LBNL = "BSD-3-Clause-LBNL"
    BSD_3_Clause_Modification = "BSD-3-Clause-Modification"
    BSD_3_Clause_No_Nuclear_License = "BSD-3-Clause-No-Nuclear-License"
    BSD_3_Clause_No_Nuclear_License_2014 = "BSD-3-Clause-No-Nuclear-License-2014"
    BSD_3_Clause_No_Nuclear_Warranty = "BSD-3-Clause-No-Nuclear-Warranty"
    BSD_3_Clause_Open_MPI = "BSD-3-Clause-Open-MPI"
    BSD_4_Clause = "BSD-4-Clause"
    BSD_4_Clause_Shortened = "BSD-4-Clause-Shortened"
    BSD_4_Clause_UC = "BSD-4-Clause-UC"
    BSD_Protection = "BSD-Protection"
    BSD_Source_Code = "BSD-Source-Code"
    BSL_1_0 = "BSL-1.0"
    BUSL_1_1 = "BUSL-1.1"
    bzip2_1_0_5 = "bzip2-1.0.5"
    bzip2_1_0_6 = "bzip2-1.0.6"
    C_UDA_1_0 = "C-UDA-1.0"
    CAL_1_0 = "CAL-1.0"
    CAL_1_0_Combined_Work_Exception = "CAL-1.0-Combined-Work-Exception"
    Caldera = "Caldera"
    CATOSL_1_1 = "CATOSL-1.1"
    CC_BY_1_0 = "CC-BY-1.0"
    CC_BY_2_0 = "CC-BY-2.0"
    CC_BY_2_5 = "CC-BY-2.5"
    CC_BY_3_0 = "CC-BY-3.0"
    CC_BY_3_0_AT = "CC-BY-3.0-AT"
    CC_BY_3_0_US = "CC-BY-3.0-US"
    CC_BY_4_0 = "CC-BY-4.0"
    CC_BY_NC_1_0 = "CC-BY-NC-1.0"
    CC_BY_NC_2_0 = "CC-BY-NC-2.0"
    CC_BY_NC_2_5 = "CC-BY-NC-2.5"
    CC_BY_NC_3_0 = "CC-BY-NC-3.0"
    CC_BY_NC_4_0 = "CC-BY-NC-4.0"
    CC_BY_NC_ND_1_0 = "CC-BY-NC-ND-1.0"
    CC_BY_NC_ND_2_0 = "CC-BY-NC-ND-2.0"
    CC_BY_NC_ND_2_5 = "CC-BY-NC-ND-2.5"
    CC_BY_NC_ND_3_0 = "CC-BY-NC-ND-3.0"
    CC_BY_NC_ND_3_0_IGO = "CC-BY-NC-ND-3.0-IGO"
    CC_BY_NC_ND_4_0 = "CC-BY-NC-ND-4.0"
    CC_BY_NC_SA_1_0 = "CC-BY-NC-SA-1.0"
    CC_BY_NC_SA_2_0 = "CC-BY-NC-SA-2.0"
    CC_BY_NC_SA_2_5 = "CC-BY-NC-SA-2.5"
    CC_BY_NC_SA_3_0 = "CC-BY-NC-SA-3.0"
    CC_BY_NC_SA_4_0 = "CC-BY-NC-SA-4.0"
    CC_BY_ND_1_0 = "CC-BY-ND-1.0"
    CC_BY_ND_2_0 = "CC-BY-ND-2.0"
    CC_BY_ND_2_5 = "CC-BY-ND-2.5"
    CC_BY_ND_3_0 = "CC-BY-ND-3.0"
    CC_BY_ND_4_0 = "CC-BY-ND-4.0"
    CC_BY_SA_1_0 = "CC-BY-SA-1.0"
    CC_BY_SA_2_0 = "CC-BY-SA-2.0"
    CC_BY_SA_2_0_UK = "CC-BY-SA-2.0-UK"
    CC_BY_SA_2_1_JP = "CC-BY-SA-2.1-JP"
    CC_BY_SA_2_5 = "CC-BY-SA-2.5"
    CC_BY_SA_3_0 = "CC-BY-SA-3.0"
    CC_BY_SA_3_0_AT = "CC-BY-SA-3.0-AT"
    CC_BY_SA_4_0 = "CC-BY-SA-4.0"
    CC_PDDC = "CC-PDDC"
    CC0_1_0 = "CC0-1.0"
    CDDL_1_0 = "CDDL-1.0"
    CDDL_1_1 = "CDDL-1.1"
    CDL_1_0 = "CDL-1.0"
    CDLA_Permissive_1_0 = "CDLA-Permissive-1.0"
    CDLA_Sharing_1_0 = "CDLA-Sharing-1.0"
    CECILL_1_0 = "CECILL-1.0"
    CECILL_1_1 = "CECILL-1.1"
    CECILL_2_0 = "CECILL-2.0"
    CECILL_2_1 = "CECILL-2.1"
    CECILL_B = "CECILL-B"
    CECILL_C = "CECILL-C"
    CERN_OHL_1_1 = "CERN-OHL-1.1"
    CERN_OHL_1_2 = "CERN-OHL-1.2"
    CERN_OHL_P_2_0 = "CERN-OHL-P-2.0"
    CERN_OHL_S_2_0 = "CERN-OHL-S-2.0"
    CERN_OHL_W_2_0 = "CERN-OHL-W-2.0"
    ClArtistic = "ClArtistic"
    CNRI_Jython = "CNRI-Jython"
    CNRI_Python = "CNRI-Python"
    CNRI_Python_GPL_Compatible = "CNRI-Python-GPL-Compatible"
    Condor_1_1 = "Condor-1.1"
    copyleft_next_0_3_0 = "copyleft-next-0.3.0"
    copyleft_next_0_3_1 = "copyleft-next-0.3.1"
    CPAL_1_0 = "CPAL-1.0"
    CPL_1_0 = "CPL-1.0"
    CPOL_1_02 = "CPOL-1.02"
    Crossword = "Crossword"
    CrystalStacker = "CrystalStacker"
    CUA_OPL_1_0 = "CUA-OPL-1.0"
    Cube = "Cube"
    curl = "curl"
    D_FSL_1_0 = "D-FSL-1.0"
    diffmark = "diffmark"
    DOC = "DOC"
    Dotseqn = "Dotseqn"
    DRL_1_0 = "DRL-1.0"
    DSDP = "DSDP"
    dvipdfm = "dvipdfm"
    ECL_1_0 = "ECL-1.0"
    ECL_2_0 = "ECL-2.0"
    eCos_2_0 = "eCos-2.0"
    EFL_1_0 = "EFL-1.0"
    EFL_2_0 = "EFL-2.0"
    eGenix = "eGenix"
    Entessa = "Entessa"
    EPICS = "EPICS"
    EPL_1_0 = "EPL-1.0"
    EPL_2_0 = "EPL-2.0"
    ErlPL_1_1 = "ErlPL-1.1"
    etalab_2_0 = "etalab-2.0"
    EUDatagrid = "EUDatagrid"
    EUPL_1_0 = "EUPL-1.0"
    EUPL_1_1 = "EUPL-1.1"
    EUPL_1_2 = "EUPL-1.2"
    Eurosym = "Eurosym"
    Fair = "Fair"
    Frameworx_1_0 = "Frameworx-1.0"
    FreeBSD_DOC = "FreeBSD-DOC"
    FreeImage = "FreeImage"
    FSFAP = "FSFAP"
    FSFUL = "FSFUL"
    FSFULLR = "FSFULLR"
    FTL = "FTL"
    GD = "GD"
    GFDL_1_1 = "GFDL-1.1"
    GFDL_1_1_invariants_only = "GFDL-1.1-invariants-only"
    GFDL_1_1_invariants_or_later = "GFDL-1.1-invariants-or-later"
    GFDL_1_1_no_invariants_only = "GFDL-1.1-no-invariants-only"
    GFDL_1_1_no_invariants_or_later = "GFDL-1.1-no-invariants-or-later"
    GFDL_1_1_only = "GFDL-1.1-only"
    GFDL_1_1_or_later = "GFDL-1.1-or-later"
    GFDL_1_2 = "GFDL-1.2"
    GFDL_1_2_invariants_only = "GFDL-1.2-invariants-only"
    GFDL_1_2_invariants_or_later = "GFDL-1.2-invariants-or-later"
    GFDL_1_2_no_invariants_only = "GFDL-1.2-no-invariants-only"
    GFDL_1_2_no_invariants_or_later = "GFDL-1.2-no-invariants-or-later"
    GFDL_1_2_only = "GFDL-1.2-only"
    GFDL_1_2_or_later = "GFDL-1.2-or-later"
    GFDL_1_3 = "GFDL-1.3"
    GFDL_1_3_invariants_only = "GFDL-1.3-invariants-only"
    GFDL_1_3_invariants_or_later = "GFDL-1.3-invariants-or-later"
    GFDL_1_3_no_invariants_only = "GFDL-1.3-no-invariants-only"
    GFDL_1_3_no_invariants_or_later = "GFDL-1.3-no-invariants-or-later"
    GFDL_1_3_only = "GFDL-1.3-only"
    GFDL_1_3_or_later = "GFDL-1.3-or-later"
    Giftware = "Giftware"
    GL2PS = "GL2PS"
    Glide = "Glide"
    Glulxe = "Glulxe"
    GLWTPL = "GLWTPL"
    gnuplot = "gnuplot"
    GPL_1_0 = "GPL-1.0"
    GPL_1_0_only = "GPL-1.0-only"
    GPL_1_0_or_later = "GPL-1.0-or-later"
    GPL_1_0_ = "GPL-1.0+"
    GPL_2_0 = "GPL-2.0"
    GPL_2_0_only = "GPL-2.0-only"
    GPL_2_0_or_later = "GPL-2.0-or-later"
    GPL_2_0_with_autoconf_exception = "GPL-2.0-with-autoconf-exception"
    GPL_2_0_with_bison_exception = "GPL-2.0-with-bison-exception"
    GPL_2_0_with_classpath_exception = "GPL-2.0-with-classpath-exception"
    GPL_2_0_with_font_exception = "GPL-2.0-with-font-exception"
    GPL_2_0_with_GCC_exception = "GPL-2.0-with-GCC-exception"
    GPL_2_0_ = "GPL-2.0+"
    GPL_3_0 = "GPL-3.0"
    GPL_3_0_only = "GPL-3.0-only"
    GPL_3_0_or_later = "GPL-3.0-or-later"
    GPL_3_0_with_autoconf_exception = "GPL-3.0-with-autoconf-exception"
    GPL_3_0_with_GCC_exception = "GPL-3.0-with-GCC-exception"
    GPL_3_0_ = "GPL-3.0+"
    gSOAP_1_3b = "gSOAP-1.3b"
    HaskellReport = "HaskellReport"
    Hippocratic_2_1 = "Hippocratic-2.1"
    HPND = "HPND"
    HPND_sell_variant = "HPND-sell-variant"
    HTMLTIDY = "HTMLTIDY"
    IBM_pibs = "IBM-pibs"
    ICU = "ICU"
    IJG = "IJG"
    ImageMagick = "ImageMagick"
    iMatix = "iMatix"
    Imlib2 = "Imlib2"
    Info_ZIP = "Info-ZIP"
    Intel = "Intel"
    Intel_ACPI = "Intel-ACPI"
    Interbase_1_0 = "Interbase-1.0"
    IPA = "IPA"
    IPL_1_0 = "IPL-1.0"
    ISC = "ISC"
    JasPer_2_0 = "JasPer-2.0"
    JPNIC = "JPNIC"
    JSON = "JSON"
    LAL_1_2 = "LAL-1.2"
    LAL_1_3 = "LAL-1.3"
    Latex2e = "Latex2e"
    Leptonica = "Leptonica"
    LGPL_2_0 = "LGPL-2.0"
    LGPL_2_0_only = "LGPL-2.0-only"
    LGPL_2_0_or_later = "LGPL-2.0-or-later"
    LGPL_2_0_ = "LGPL-2.0+"
    LGPL_2_1 = "LGPL-2.1"
    LGPL_2_1_only = "LGPL-2.1-only"
    LGPL_2_1_or_later = "LGPL-2.1-or-later"
    LGPL_2_1_ = "LGPL-2.1+"
    LGPL_3_0 = "LGPL-3.0"
    LGPL_3_0_only = "LGPL-3.0-only"
    LGPL_3_0_or_later = "LGPL-3.0-or-later"
    LGPL_3_0_ = "LGPL-3.0+"
    LGPLLR = "LGPLLR"
    Libpng = "Libpng"
    libpng_2_0 = "libpng-2.0"
    libselinux_1_0 = "libselinux-1.0"
    libtiff = "libtiff"
    LiLiQ_P_1_1 = "LiLiQ-P-1.1"
    LiLiQ_R_1_1 = "LiLiQ-R-1.1"
    LiLiQ_Rplus_1_1 = "LiLiQ-Rplus-1.1"
    Linux_OpenIB = "Linux-OpenIB"
    LPL_1_0 = "LPL-1.0"
    LPL_1_02 = "LPL-1.02"
    LPPL_1_0 = "LPPL-1.0"
    LPPL_1_1 = "LPPL-1.1"
    LPPL_1_2 = "LPPL-1.2"
    LPPL_1_3a = "LPPL-1.3a"
    LPPL_1_3c = "LPPL-1.3c"
    MakeIndex = "MakeIndex"
    MirOS = "MirOS"
    MIT = "MIT"
    MIT_0 = "MIT-0"
    MIT_advertising = "MIT-advertising"
    MIT_CMU = "MIT-CMU"
    MIT_enna = "MIT-enna"
    MIT_feh = "MIT-feh"
    MIT_Modern_Variant = "MIT-Modern-Variant"
    MIT_open_group = "MIT-open-group"
    MITNFA = "MITNFA"
    Motosoto = "Motosoto"
    mpich2 = "mpich2"
    MPL_1_0 = "MPL-1.0"
    MPL_1_1 = "MPL-1.1"
    MPL_2_0 = "MPL-2.0"
    MPL_2_0_no_copyleft_exception = "MPL-2.0-no-copyleft-exception"
    MS_PL = "MS-PL"
    MS_RL = "MS-RL"
    MTLL = "MTLL"
    MulanPSL_1_0 = "MulanPSL-1.0"
    MulanPSL_2_0 = "MulanPSL-2.0"
    Multics = "Multics"
    Mup = "Mup"
    NAIST_2003 = "NAIST-2003"
    NASA_1_3 = "NASA-1.3"
    Naumen = "Naumen"
    NBPL_1_0 = "NBPL-1.0"
    NCGL_UK_2_0 = "NCGL-UK-2.0"
    NCSA = "NCSA"
    Net_SNMP = "Net-SNMP"
    NetCDF = "NetCDF"
    Newsletr = "Newsletr"
    NGPL = "NGPL"
    NIST_PD = "NIST-PD"
    NIST_PD_fallback = "NIST-PD-fallback"
    NLOD_1_0 = "NLOD-1.0"
    NLPL = "NLPL"
    Nokia = "Nokia"
    NOSL = "NOSL"
    Noweb = "Noweb"
    NPL_1_0 = "NPL-1.0"
    NPL_1_1 = "NPL-1.1"
    NPOSL_3_0 = "NPOSL-3.0"
    NRL = "NRL"
    NTP = "NTP"
    NTP_0 = "NTP-0"
    Nunit = "Nunit"
    O_UDA_1_0 = "O-UDA-1.0"
    OCCT_PL = "OCCT-PL"
    OCLC_2_0 = "OCLC-2.0"
    ODbL_1_0 = "ODbL-1.0"
    ODC_By_1_0 = "ODC-By-1.0"
    OFL_1_0 = "OFL-1.0"
    OFL_1_0_no_RFN = "OFL-1.0-no-RFN"
    OFL_1_0_RFN = "OFL-1.0-RFN"
    OFL_1_1 = "OFL-1.1"
    OFL_1_1_no_RFN = "OFL-1.1-no-RFN"
    OFL_1_1_RFN = "OFL-1.1-RFN"
    OGC_1_0 = "OGC-1.0"
    OGDL_Taiwan_1_0 = "OGDL-Taiwan-1.0"
    OGL_Canada_2_0 = "OGL-Canada-2.0"
    OGL_UK_1_0 = "OGL-UK-1.0"
    OGL_UK_2_0 = "OGL-UK-2.0"
    OGL_UK_3_0 = "OGL-UK-3.0"
    OGTSL = "OGTSL"
    OLDAP_1_1 = "OLDAP-1.1"
    OLDAP_1_2 = "OLDAP-1.2"
    OLDAP_1_3 = "OLDAP-1.3"
    OLDAP_1_4 = "OLDAP-1.4"
    OLDAP_2_0 = "OLDAP-2.0"
    OLDAP_2_0_1 = "OLDAP-2.0.1"
    OLDAP_2_1 = "OLDAP-2.1"
    OLDAP_2_2 = "OLDAP-2.2"
    OLDAP_2_2_1 = "OLDAP-2.2.1"
    OLDAP_2_2_2 = "OLDAP-2.2.2"
    OLDAP_2_3 = "OLDAP-2.3"
    OLDAP_2_4 = "OLDAP-2.4"
    OLDAP_2_5 = "OLDAP-2.5"
    OLDAP_2_6 = "OLDAP-2.6"
    OLDAP_2_7 = "OLDAP-2.7"
    OLDAP_2_8 = "OLDAP-2.8"
    OML = "OML"
    OpenSSL = "OpenSSL"
    OPL_1_0 = "OPL-1.0"
    OSET_PL_2_1 = "OSET-PL-2.1"
    OSL_1_0 = "OSL-1.0"
    OSL_1_1 = "OSL-1.1"
    OSL_2_0 = "OSL-2.0"
    OSL_2_1 = "OSL-2.1"
    OSL_3_0 = "OSL-3.0"
    Parity_6_0_0 = "Parity-6.0.0"
    Parity_7_0_0 = "Parity-7.0.0"
    PDDL_1_0 = "PDDL-1.0"
    PHP_3_0 = "PHP-3.0"
    PHP_3_01 = "PHP-3.01"
    Plexus = "Plexus"
    PolyForm_Noncommercial_1_0_0 = "PolyForm-Noncommercial-1.0.0"
    PolyForm_Small_Business_1_0_0 = "PolyForm-Small-Business-1.0.0"
    PostgreSQL = "PostgreSQL"
    PSF_2_0 = "PSF-2.0"
    psfrag = "psfrag"
    psutils = "psutils"
    Python_2_0 = "Python-2.0"
    Qhull = "Qhull"
    QPL_1_0 = "QPL-1.0"
    Rdisc = "Rdisc"
    RHeCos_1_1 = "RHeCos-1.1"
    RPL_1_1 = "RPL-1.1"
    RPL_1_5 = "RPL-1.5"
    RPSL_1_0 = "RPSL-1.0"
    RSA_MD = "RSA-MD"
    RSCPL = "RSCPL"
    Ruby = "Ruby"
    SAX_PD = "SAX-PD"
    Saxpath = "Saxpath"
    SCEA = "SCEA"
    Sendmail = "Sendmail"
    Sendmail_8_23 = "Sendmail-8.23"
    SGI_B_1_0 = "SGI-B-1.0"
    SGI_B_1_1 = "SGI-B-1.1"
    SGI_B_2_0 = "SGI-B-2.0"
    SHL_0_5 = "SHL-0.5"
    SHL_0_51 = "SHL-0.51"
    SimPL_2_0 = "SimPL-2.0"
    SISSL = "SISSL"
    SISSL_1_2 = "SISSL-1.2"
    Sleepycat = "Sleepycat"
    SMLNJ = "SMLNJ"
    SMPPL = "SMPPL"
    SNIA = "SNIA"
    Spencer_86 = "Spencer-86"
    Spencer_94 = "Spencer-94"
    Spencer_99 = "Spencer-99"
    SPL_1_0 = "SPL-1.0"
    SSH_OpenSSH = "SSH-OpenSSH"
    SSH_short = "SSH-short"
    SSPL_1_0 = "SSPL-1.0"
    StandardML_NJ = "StandardML-NJ"
    SugarCRM_1_1_3 = "SugarCRM-1.1.3"
    SWL = "SWL"
    TAPR_OHL_1_0 = "TAPR-OHL-1.0"
    TCL = "TCL"
    TCP_wrappers = "TCP-wrappers"
    TMate = "TMate"
    TORQUE_1_1 = "TORQUE-1.1"
    TOSL = "TOSL"
    TU_Berlin_1_0 = "TU-Berlin-1.0"
    TU_Berlin_2_0 = "TU-Berlin-2.0"
    UCL_1_0 = "UCL-1.0"
    Unicode_DFS_2015 = "Unicode-DFS-2015"
    Unicode_DFS_2016 = "Unicode-DFS-2016"
    Unicode_TOU = "Unicode-TOU"
    Unlicense = "Unlicense"
    UPL_1_0 = "UPL-1.0"
    Vim = "Vim"
    VOSTROM = "VOSTROM"
    VSL_1_0 = "VSL-1.0"
    W3C = "W3C"
    W3C_19980720 = "W3C-19980720"
    W3C_20150513 = "W3C-20150513"
    Watcom_1_0 = "Watcom-1.0"
    Wsuipa = "Wsuipa"
    WTFPL = "WTFPL"
    wxWindows = "wxWindows"
    X11 = "X11"
    Xerox = "Xerox"
    XFree86_1_1 = "XFree86-1.1"
    xinetd = "xinetd"
    Xnet = "Xnet"
    xpp = "xpp"
    XSkat = "XSkat"
    YPL_1_0 = "YPL-1.0"
    YPL_1_1 = "YPL-1.1"
    Zed = "Zed"
    Zend_2_0 = "Zend-2.0"
    Zimbra_1_3 = "Zimbra-1.3"
    Zimbra_1_4 = "Zimbra-1.4"
    Zlib = "Zlib"
    zlib_acknowledgement = "zlib-acknowledgement"
    ZPL_1_1 = "ZPL-1.1"
    ZPL_2_0 = "ZPL-2.0"
    ZPL_2_1 = "ZPL-2.1"


class ContributionTypeEnum(Enum):
    """Contribution type using emojis from https://allcontributors.org/docs/en/emoji-key ."""

    audio = "audio"
    ally = "ally"
    bug = "bug"
    blog = "blog"
    business = "business"
    code = "code"
    content = "content"
    data = "data"
    doc = "doc"
    design = "design"
    example = "example"
    eventOrganizing = "eventOrganizing"
    financial = "financial"
    fundingFinding = "fundingFinding"
    ideas = "ideas"
    infra = "infra"
    maintenance = "maintenance"
    mentoring = "mentoring"
    platform = "platform"
    plugin = "plugin"
    projectManagement = "projectManagement"
    promotion = "promotion"
    question = "question"
    research = "research"
    review = "review"
    security = "security"
    tool = "tool"
    translation = "translation"
    test = "test"
    tutorial = "tutorial"
    talk = "talk"
    userTesting = "userTesting"
    video = "video"


class Country(Enum):
    """Country codes from https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2 . It is used for the country of a person in project metadata."""

    AD = "AD"
    AE = "AE"
    AF = "AF"
    AG = "AG"
    AI = "AI"
    AL = "AL"
    AM = "AM"
    AO = "AO"
    AQ = "AQ"
    AR = "AR"
    AS = "AS"
    AT = "AT"
    AU = "AU"
    AW = "AW"
    AX = "AX"
    AZ = "AZ"
    BA = "BA"
    BB = "BB"
    BD = "BD"
    BE = "BE"
    BF = "BF"
    BG = "BG"
    BH = "BH"
    BI = "BI"
    BJ = "BJ"
    BL = "BL"
    BM = "BM"
    BN = "BN"
    BO = "BO"
    BQ = "BQ"
    BR = "BR"
    BS = "BS"
    BT = "BT"
    BV = "BV"
    BW = "BW"
    BY = "BY"
    BZ = "BZ"
    CA = "CA"
    CC = "CC"
    CD = "CD"
    CF = "CF"
    CG = "CG"
    CH = "CH"
    CI = "CI"
    CK = "CK"
    CL = "CL"
    CM = "CM"
    CN = "CN"
    CO = "CO"
    CR = "CR"
    CU = "CU"
    CV = "CV"
    CW = "CW"
    CX = "CX"
    CY = "CY"
    CZ = "CZ"
    DE = "DE"
    DJ = "DJ"
    DK = "DK"
    DM = "DM"
    DO = "DO"
    DZ = "DZ"
    EC = "EC"
    EE = "EE"
    EG = "EG"
    EH = "EH"
    ER = "ER"
    ES = "ES"
    ET = "ET"
    FI = "FI"
    FJ = "FJ"
    FK = "FK"
    FM = "FM"
    FO = "FO"
    FR = "FR"
    GA = "GA"
    GB = "GB"
    GD = "GD"
    GE = "GE"
    GF = "GF"
    GG = "GG"
    GH = "GH"
    GI = "GI"
    GL = "GL"
    GM = "GM"
    GN = "GN"
    GP = "GP"
    GQ = "GQ"
    GR = "GR"
    GS = "GS"
    GT = "GT"
    GU = "GU"
    GW = "GW"
    GY = "GY"
    HK = "HK"
    HM = "HM"
    HN = "HN"
    HR = "HR"
    HT = "HT"
    HU = "HU"
    ID = "ID"
    IE = "IE"
    IL = "IL"
    IM = "IM"
    IN = "IN"
    IO = "IO"
    IQ = "IQ"
    IR = "IR"
    IS = "IS"
    IT = "IT"
    JE = "JE"
    JM = "JM"
    JO = "JO"
    JP = "JP"
    KE = "KE"
    KG = "KG"
    KH = "KH"
    KI = "KI"
    KM = "KM"
    KN = "KN"
    KP = "KP"
    KR = "KR"
    KW = "KW"
    KY = "KY"
    KZ = "KZ"
    LA = "LA"
    LB = "LB"
    LC = "LC"
    LI = "LI"
    LK = "LK"
    LR = "LR"
    LS = "LS"
    LT = "LT"
    LU = "LU"
    LV = "LV"
    LY = "LY"
    MA = "MA"
    MC = "MC"
    MD = "MD"
    ME = "ME"
    MF = "MF"
    MG = "MG"
    MH = "MH"
    MK = "MK"
    ML = "ML"
    MM = "MM"
    MN = "MN"
    MO = "MO"
    MP = "MP"
    MQ = "MQ"
    MR = "MR"
    MS = "MS"
    MT = "MT"
    MU = "MU"
    MV = "MV"
    MW = "MW"
    MX = "MX"
    MY = "MY"
    MZ = "MZ"
    NA = "NA"
    NC = "NC"
    NE = "NE"
    NF = "NF"
    NG = "NG"
    NI = "NI"
    NL = "NL"
    NO = "NO"
    NP = "NP"
    NR = "NR"
    NU = "NU"
    NZ = "NZ"
    OM = "OM"
    PA = "PA"
    PE = "PE"
    PF = "PF"
    PG = "PG"
    PH = "PH"
    PK = "PK"
    PL = "PL"
    PM = "PM"
    PN = "PN"
    PR = "PR"
    PS = "PS"
    PT = "PT"
    PW = "PW"
    PY = "PY"
    QA = "QA"
    RE = "RE"
    RO = "RO"
    RS = "RS"
    RU = "RU"
    RW = "RW"
    SA = "SA"
    SB = "SB"
    SC = "SC"
    SD = "SD"
    SE = "SE"
    SG = "SG"
    SH = "SH"
    SI = "SI"
    SJ = "SJ"
    SK = "SK"
    SL = "SL"
    SM = "SM"
    SN = "SN"
    SO = "SO"
    SR = "SR"
    SS = "SS"
    ST = "ST"
    SV = "SV"
    SX = "SX"
    SY = "SY"
    SZ = "SZ"
    TC = "TC"
    TD = "TD"
    TF = "TF"
    TG = "TG"
    TH = "TH"
    TJ = "TJ"
    TK = "TK"
    TL = "TL"
    TM = "TM"
    TN = "TN"
    TO = "TO"
    TR = "TR"
    TT = "TT"
    TV = "TV"
    TW = "TW"
    TZ = "TZ"
    UA = "UA"
    UG = "UG"
    UM = "UM"
    US = "US"
    UY = "UY"
    UZ = "UZ"
    VA = "VA"
    VC = "VC"
    VE = "VE"
    VG = "VG"
    VI = "VI"
    VN = "VN"
    VU = "VU"
    WF = "WF"
    WS = "WS"
    YE = "YE"
    YT = "YT"
    ZA = "ZA"
    ZM = "ZM"
    ZW = "ZW"


class Person(BaseModel):
    """A person that is used in project metadata. Required fields are given-names, family-names, and  email."""

    class Config:
        """Configuration for the Person model."""

        extra = Extra.forbid

    address: Optional[
        Annotated[str, Field(min_length=1, description="The person's address.")]
    ]
    affiliation: Optional[
        Annotated[str, Field(min_length=1, description="The person's affiliation.")]
    ]
    alias: Optional[
        Annotated[str, Field(min_length=1, description="The person's alias.")]
    ]
    city: Optional[
        Annotated[str, Field(min_length=1, description="The person's city.")]
    ]
    country: Optional[Country] = Field(None, description="The person's country.")
    email: Annotated[
        str,
        Field(
            regex=r"^[\S]+@[\S]+\.[\S]{2,}$",
            description="The person's email address.",
        ),
    ]
    family_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="family-names",
            description="The person's family names.",
        ),
    ]
    fax: Optional[
        Annotated[str, Field(min_length=1, description="The person's fax number.")]
    ]
    given_names: Annotated[
        str,
        Field(
            min_length=1,
            alias="given-names",
            description="The person's given names.",
        ),
    ]
    name_particle: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-particle",
                description="The person's name particle, e.g., a nobiliary particle or a preposition meaning 'of' or 'from' (for example 'von' in 'Alexander von Humboldt').",
                examples=["von"],
            ),
        ]
    ]
    name_suffix: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                alias="name-suffix",
                description="The person's name-suffix, e.g. 'Jr.' for Sammy Davis Jr. or 'III' for Frank Edwin Wright III.",
                examples=["Jr.", "III"],
            ),
        ]
    ]
    orcid: Optional[AnyUrl] = Field(None, description="The person's ORCID url.")
    post_code: Optional[
        Annotated[
            str,
            Field(
                min_length=1, alias="post-code", description="The person's post-code."
            ),
        ]
    ]
    region: Optional[
        Annotated[str, Field(min_length=1, description="The person's region.")]
    ]
    tel: Optional[
        Annotated[str, Field(min_length=1, description="The person's phone number.")]
    ]
    website: Optional[AnyUrl] = Field(None, description="The person's website.")
    contribution: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                description="Summary of how the person contributed to the project.",
            ),
        ]
    ]
    contribution_type: Optional[
        Union[ContributionTypeEnum, List[ContributionTypeEnum]]
    ] = Field(None, description="Contribution type of contributor.")
    contribution_begin: Optional[date] = Field(
        None, description="Beginning date of the contribution."
    )
    contribution_end: Optional[date] = Field(
        None, description="Ending date of the contribution."
    )

    @property
    def full_name(self) -> str:
        """Return the full name of the person."""
        names = []

        if self.given_names:
            names.append(self.given_names)

        if self.name_particle:
            names.append(self.name_particle)

        if self.family_names:
            names.append(self.family_names)

        if self.name_suffix:
            names.append(self.name_suffix)

        if not names:
            return ""
        return " ".join(names)


class ProjectMetadata(BaseModel):
    """Pydantic model for Project Metadata Input. Required fields are name, description, authors, and license."""

    name: Annotated[str, Field(min_length=2, description="Package name.")]
    description: Annotated[str, Field(min_length=1, description="Package description.")]
    version: Optional[
        Annotated[str, Field(min_length=1, description="Package version.")]
    ]
    authors: List[Person] = Field(None, description="Package authors.")
    maintainers: Optional[List[Person]] = Field(
        None, description="Package maintainers."
    )
    contributors: Optional[List[Person]] = Field(
        None, description="Package contributors."
    )
    keywords: Optional[List[str]] = Field(
        None, description="Keywords that describe the package."
    )
    license: LicenseEnum = Field(None, description="SPDX License string.")
    repository: Optional[AnyUrl] = Field(None, description="URL of the repository.")
    homepage: Optional[AnyUrl] = Field(None, description="URL of the package homepage.")


class ProjectMetadataWriter(ABC):
    """Base class for Project Metadata Output Wrapper."""

    def __init__(
        self, path: Path, create_if_not_exists: Optional[bool] = False
    ) -> None:
        """Initialize the Project Metadata Output Wrapper."""
        self.path = path
        self.create_if_not_exists = create_if_not_exists

        # fill in load
        self._data: dict = {}

    @abstractmethod
    def _load(self):
        """Load the output file and validate it."""

    @abstractmethod
    def _validate(self):
        """Validate the output file."""

    def _create_empty_file(self) -> None:
        """Create an empty file if it does not exist."""
        self.path.touch()

    def _get_property(self, key: str) -> Optional[Any]:
        """Get a property from the data."""
        try:
            return self._data[key]
        except KeyError:
            return None

    def _set_property(self, key: str, value: Any) -> None:
        """Set a property in the data."""
        if value:
            self._data[key] = value
        return None

    @property
    def name(self):
        """Return the name of the project."""
        return self._get_property("name")

    @name.setter
    def name(self, name: str) -> None:
        """Set the name of the project."""
        self._set_property("name", name)

    @property
    def version(self) -> Optional[str]:
        """Return the version of the project."""
        return self._get_property("version")

    @version.setter
    def version(self, version: str) -> None:
        """Set the version of the project."""
        self._set_property("version", version)

    @property
    def description(self) -> Optional[str]:
        """Return the description of the project."""
        return self._get_property("description")

    @description.setter
    def description(self, description: str) -> None:
        """Set the description of the project."""
        self._set_property("description", description)

    @property
    def authors(self):
        """Return the authors of the project."""
        return self._get_property("authors")

    @authors.setter
    @abstractmethod
    def authors(self, authors: List[Person]) -> None:
        """Set the authors of the project."""

    @property
    def maintainers(self):
        """Return the maintainers of the project."""
        return self._get_property("maintainers")

    @maintainers.setter
    @abstractmethod
    def maintainers(self, maintainers: List[Person]) -> None:
        """Set the maintainers of the project."""

    @property
    def keywords(self) -> Optional[List[str]]:
        """Return the keywords of the project."""
        return self._get_property("keywords")

    @keywords.setter
    def keywords(self, keywords: List[str]) -> None:
        """Set the keywords of the project."""
        self._set_property("keywords", keywords)

    @property
    def license(self) -> Optional[str]:
        """Return the license of the project."""
        return self._get_property("license")

    @license.setter
    def license(self, license: Optional[str]) -> None:
        """Set the license of the project."""
        self._set_property("license", license)

    @property
    def homepage(self) -> Optional[str]:
        """Return the homepage url of the project."""
        return self._get_property("homepage")

    @homepage.setter
    def homepage(self, homepage: Optional[str]) -> None:
        """Set the homepage url of the project."""
        self._set_property("homepage", homepage)

    @property
    def repository(self) -> Optional[str]:
        """Return the repository url of the project."""
        return self._get_property("repository")

    @repository.setter
    def repository(self, repository: Optional[str]) -> None:
        """Set the repository url of the project."""
        self._set_property("repository", repository)

    def sync(self, metadata: ProjectMetadata) -> None:
        """Sync output file with other metadata files."""
        self.name = metadata.name
        self.description = metadata.description

        if metadata.version:
            self.version = metadata.version

        if metadata.keywords:
            self.keywords = metadata.keywords
        self.authors = metadata.authors
        if metadata.maintainers:
            self.maintainers = metadata.maintainers

        self.license = metadata.license.value
        self.homepage = str(metadata.homepage)
        self.repository = str(metadata.repository)

    @abstractmethod
    def save(self, path: Optional[Path]) -> None:
        """Save the output file to the given path."""


class SomesyCLIConfig(BaseModel):
    """Pydantic model for Somesy Config Input. This is input will be used as default if there is no CLI option given."""

    input_file: Optional[Path] = Field(
        Path(".somesy.toml"), description="Input file path."
    )
    no_sync_cff: Optional[bool] = Field(False, description="Do not sync with CFF.")
    cff_file: Optional[Path] = Field(Path("CITATION.cff"), description="CFF file path.")
    no_sync_pyproject: Optional[bool] = Field(
        False, description="Do not sync with pyproject.toml."
    )
    pyproject_file: Optional[Path] = Field(
        Path("pyproject.toml"), description="pyproject.toml file path."
    )
    no_sync_codemeta: Optional[bool] = Field(
        False, description="Do not sync with codemeta.json."
    )
    codemeta_file: Optional[Path] = Field(
        Path("codemeta.json"), description="codemeta.json file path."
    )
    show_info: Optional[bool] = Field(
        False, description="Show basic information messages on run."
    )
    verbose: Optional[bool] = Field(False, description="Show verbose messages on run.")
    debug: Optional[bool] = Field(False, description="Show debug messages on run.")

    class Config:
        """Pydantic model config."""

        extra = "forbid"
