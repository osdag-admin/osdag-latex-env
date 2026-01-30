import os
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
        self.prefix = Path(sys.prefix)
        self.system = platform.system().lower()
        self.bin_dir = self._detect_bin_dir()
        self.tex_root = self._detect_tex_root()
        self.bin = self._discover_binaries()


    def configure_tex(self):
        
        texmf_dist = str(self.tex_root / "texmf-dist")

        os.environ["TEXMFHOME"] = texmf_dist
        os.environ["TEXINPUTS"] = texmf_dist + os.pathsep + os.environ.get("TEXINPUTS", "")
        sty_pkgs = str(self.tex_root / "texmf-dist" / "tex" / "latex").replace("\\", "/")
        pkg_resources = [
            f"{sty_pkgs}/amsmath",
            f"{sty_pkgs}/graphics",
            f"{sty_pkgs}/needspace",
        ]

        os.environ["TEXINPUTS"] = ";".join(pkg_resources) + ";" + os.environ["TEXINPUTS"]
        
    @property
    def available(self) -> bool:
        """
        Check whether any LaTeX binaries were found in this environment.

        Returns
        -------
        bool
            True if at least one LaTeX executable is available, False otherwise.
        """
        return bool(self.bin)
    
    def _detect_bin_dir(self) -> Path:
        """
        Detect the directory containing executables for the current platform.

        On Windows (Conda layout):
            <env>/Library/bin

        On Linux/macOS:
            <env>/bin

        Returns
        -------
        Path
            Path to the directory containing LaTeX executables.
        """
        if self.system == "windows":
            return self.prefix / "Library" / "share" / "osdag_latex_env" / "bin"
        else:
            return self.prefix / "share" / "osdag_latex_env" / "bin"

    def _detect_tex_root(self) -> Path:
        """
        Detect the root directory containing the LaTeX data tree (texmf).

        This is where packages, fonts, and configuration files live.

        Returns
        -------
        Path
            Path to the osdag-latex-env texmf root.
        """
        if self.system == "windows":
            return self.prefix / "Library" / "share" / "osdag_latex_env"
        else:
            return self.prefix / "share" / "osdag_latex_env"

    def _discover_binaries(self) -> dict[str, Path]:
        """
        Scan the binary directory and build a registry of available executables.

        The registry maps lowercase executable names (without extensions)
        to their absolute filesystem paths.

        Example:
            {
                "pdflatex": Path(.../pdflatex),
                "bibtex": Path(.../bibtex),
                "latexmk": Path(.../latexmk)
            }

        Returns
        -------
        dict[str, Path]
            Mapping of executable names to their paths.
        """
        bins = {}
        if not self.bin_dir.exists():
            return bins
        for p in self.bin_dir.iterdir():
            if p.is_file():
                bins[p.stem.lower()] = p
        return bins

    def has(self, name) -> bool:
        """
        Check whether a given LaTeX tool exists in this environment.

        Parameters
        ----------
        name : str
            Name of the executable (e.g. "pdflatex", "latexmk").

        Returns
        -------
        bool
            True if the executable is available, False otherwise.
        """
        return name.lower() in self.bin

    def get(self, name) -> Path:
        """
        Get the filesystem path of a LaTeX executable.

        Parameters
        ----------
        name : str
            Name of the executable (e.g. "pdflatex").

        Returns
        -------
        Path
            Absolute path to the executable.

        Raises
        ------
        RuntimeError
            If the executable is not found in this environment.
        """
        try:
            return self.bin[name.lower()]
        except KeyError:
            raise RuntimeError(f"{name} not found in {self.__class__.__name__}")
        
    def get_pdflatex(self) -> Path:
        """
        Get the path to the pdflatex executable.

        Returns
        -------
        Path
            Absolute path to pdflatex.
        """
        return self.get("pdflatex")
    
    