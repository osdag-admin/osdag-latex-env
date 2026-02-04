import os
import shutil
import sys
import platform
import subprocess
from pathlib import Path

class OsdagLatexEnv:
    """
    OsdagLatexEnv provides a lightweight interface to the LaTeX toolchain
    installed inside the currently active Conda environment.

    The class does not install or configure LaTeX. Instead, it *discovers*
    the existing LaTeX runtime (binaries and data directories) and exposes:

    - Paths to LaTeX executables (e.g. pdflatex, bibtex)
    - A registry of all available TeX-related binaries
    - Convenience methods to invoke common tools

    This design treats LaTeX as a system-level toolchain and Python as a
    discovery layer.
    """
    def __init__(self):
        """
        Initialize the LaTeX environment by discovering the active Conda
        prefix, detecting the operating system, and scanning for available
        LaTeX binaries.
        """
        self.__prefix = Path(sys.prefix)
        self.__system = platform.system().lower()
        self.__machine = platform.machine().lower()
        self.bin_dir = self._detect_bin_dir() 
        self.tex_root = self._detect_tex_root() 
        self.pdflatex = self._get_pdflatex() 

    # Need correction
    # def configure_tex(self):
        
    #     if (self.tex_root.exists() and self.pdflatex.exists()):
    #         texmf_dist = str(self.tex_root / "texmf-dist")

    #         os.environ["TEXMFHOME"] = texmf_dist
    #         os.environ["TEXINPUTS"] = texmf_dist + os.pathsep + os.environ.get("TEXINPUTS", "")
    #         sty_pkgs = str(self.tex_root / "texmf-dist" / "tex" / "latex").replace("\\", "/")
    #         pkg_resources = [
    #             f"{sty_pkgs}/amsmath",
    #             f"{sty_pkgs}/graphics",
    #             f"{sty_pkgs}/needspace",
    #         ]

    #         os.environ["TEXINPUTS"] = ";".join(pkg_resources) + ";" + os.environ["TEXINPUTS"]
        
    @property
    def available(self) -> bool:
        """
        Check whether if Module found in this env.

        Returns
        -------
        bool
            True if osdag_latex_env is available, False otherwise.
        """
        if not (self.tex_root and self.pdflatex):
            return False
        try:
            subprocess.run(
                [str(self.pdflatex), "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return True
        except Exception:
            return False
    
    def _detect_bin_dir(self) -> Path | None:
        """
        Detect the directory containing executables for the current platform.

        On Windows (Conda layout):
            <env>/Library/share/osdag_latex_env/bin

        On Linux/macOS:
            <env>/share/osdag_latex_env/bin

        Returns
        -------
        Path | None
            Path to the directory containing LaTeX executables.
        """
        if self.__system == "windows":
            dir = self.__prefix / "Library" / "share" / "osdag_latex_env" / "bin" / "x86_64-windows"
            return dir if dir.exists() else None
        elif self.__system == "linux":
            dir = self.__prefix / "share" / "osdag_latex_env" / "bin" / "x86_64-linux"
            return dir if dir.exists() else None
        elif self.__system == "darwin":
            dir = self.__prefix / "share" / "osdag_latex_env" / "bin" / "universal-darwin"
            return dir if dir.exists() else None

    def _detect_tex_root(self) -> Path | None:
        """
        Detect the root directory containing the LaTeX data tree (texmf).

        This is where packages, fonts, and configuration files live.

        Returns
        -------
        Path
            Path to the osdag-latex-env texmf root.
        """
        if self.__system == "windows":
            dir = self.__prefix / "Library" / "share" / "osdag_latex_env"
            return dir if dir.exists() else None
        else:
            dir = self.__prefix / "share" / "osdag_latex_env"
            return dir if dir.exists() else None
        
    def _get_pdflatex(self) -> Path | None:
        """
        Get the path to the pdflatex executable.

        Returns
        -------
        Path | None
            Absolute path to pdflatex, None if not found.
        """
        exe = "pdflatex.exe" if self.__system == "windows" else "pdflatex"
        if self.bin_dir and (self.bin_dir / exe).exists():
            return self.bin_dir / exe
        sys_latex = shutil.which("pdflatex")
        if sys_latex is not None:
            return Path(sys_latex)
        return None
    
    
