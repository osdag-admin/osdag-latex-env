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
    
    def require(self):
        """
        Ensure that LaTeX binaries are available in this environment. Use if want to force osdag-latex-env presence.

        Raises
        ------
        RuntimeError
            If no LaTeX binaries are found.
        """
        if not self.available:
            raise RuntimeError("No LaTeX binaries found in the current environment. Please install osdag-latex-env.")

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
            return self.prefix / "Library" / "bin"
        else:
            return self.prefix / "bin"

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
            return self.prefix / "Library" / "share" / "osdag-latex-env"
        else:
            return self.prefix / "share" / "osdag-latex-env"

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
    
    def get_bibtex(self) -> Path:
        """
        Get the path to the bibtex executable.

        Returns
        -------
        Path
            Absolute path to bibtex.
        """
        return self.get("bibtex")

    def run(self, name, args=None) -> subprocess.CompletedProcess:
        """
        Run a LaTeX-related executable with the given arguments.

        This is a generic execution method for any tool in the registry.

        Parameters
        ----------
        name : str
            Name of the executable to run.
        args : list[str], optional
            Command-line arguments passed to the executable.

        Returns
        -------
        subprocess.CompletedProcess
            Result object returned by subprocess.run.
        """

        if args is None:
            args = []
        exe = self.get(name)
        return subprocess.run([str(exe)] + args)

    def pdflatex(self, tex_file, extra_args=None) -> subprocess.CompletedProcess:
        """
        Compile a TeX file using pdflatex.

        This is a convenience wrapper around `run("pdflatex", ...)`.

        Parameters
        ----------
        tex_file : str
            Path to the .tex file.
        extra_args : list[str], optional
            Additional command-line flags for pdflatex.

        Returns
        -------
        subprocess.CompletedProcess
            Result object returned by subprocess.run.
        """
        args = []
        if extra_args:
            args += extra_args
        args.append(tex_file)
        return self.run("pdflatex", args)
