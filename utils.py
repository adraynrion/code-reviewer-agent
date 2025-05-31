
def get_file_languages(filename: str) -> list[str]:
    """
    Detect programming languages used based on the filename.

    Args:
        filename: The filename to detect the language for

    Returns:
        The detected programming languages.
    """

    # Simple file extension based detection
    ext = filename.split('.')[-1].lower()
    match ext:
        # Programming languages
        case 'py':
            return ['python']
        case 'js' | 'jsx' | 'mjs' | 'cjs':
            return ['javascript']
        case 'ts' | 'tsx':
            return ['typescript', 'javascript']
        case 'java':
            return ['java']
        case 'go':
            return ['go']
        case 'rb':
            return ['ruby']
        case 'php' | 'phtml' | 'php3' | 'php4' | 'php5' | 'php7' | 'phps':
            return ['php']
        case 'cs':
            return ['csharp']
        case 'cpp' | 'cxx' | 'cc' | 'hpp' | 'hxx' | 'hh':
            return ['c++']
        case 'c' | 'h':
            return ['c']
        case 'swift':
            return ['swift']
        case 'kt' | 'kts':
            return ['kotlin']
        case 'rs':
            return ['rust']
        case 'scala' | 'sc':
            return ['scala']

        # Web and markup languages
        case 'html' | 'htm' | 'xhtml' | 'html5':
            return ['html']
        case 'css':
            return ['css']
        case 'scss':
            return ['scss', 'css']
        case 'sass':
            return ['sass', 'css']
        case 'less':
            return ['less', 'css']

        # Template and configuration
        case 'json':
            return ['json']
        case 'yaml' | 'yml':
            return ['yaml']
        case 'xml':
            return ['xml']
        case 'md' | 'markdown':
            return ['markdown']

        # Shell and scripts
        case 'sh' | 'bash' | 'zsh' | 'fish':
            return ['shell']
        case 'ps1' | 'psm1' | 'psd1':
            return ['powershell']

        # Database
        case 'sql':
            return ['sql']

        # Configuration files
        case 'env' | 'env.example':
            return ['dotenv']
        case 'toml':
            return ['toml']
        case 'ini' | 'cfg' | 'prefs':
            return ['ini']
        case 'dockerfile' | 'dockerignore':
            return ['dockerfile']
        case 'gitignore' | 'gitattributes' | 'gitmodules':
            return ['git']
        case 'editorconfig':
            return ['editorconfig']
        case _:
            return ['unknown']
