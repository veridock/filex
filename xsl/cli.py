"""
CLI interface for xsl.
"""

"""
Command-line interface for xsl.

This module provides the CLI interface for the xsl package.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from . import __version__, FileEditor


class CLI:
    """Command-line interface for xsl."""

    def __init__(self):
        self.editor: Optional[FileEditor] = None

    def run(self):
        """Run the CLI with command line arguments."""
        parser = argparse.ArgumentParser(
            description="xsl - Universal File Editor for XML/SVG/HTML",
            epilog="For more information, visit: https://github.com/veridock/xsl",
        )
        parser.add_argument("--version", action="version", version=f"xsl {__version__}")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Load command
        load_parser = subparsers.add_parser("load", help="Load file (local or remote)")
        load_parser.add_argument("file", help="File path or URL")

        # Query command
        query_parser = subparsers.add_parser("query", help="Query elements using XPath")
        query_parser.add_argument("xpath", help="XPath expression")
        query_parser.add_argument(
            "--type",
            choices=["text", "attribute"],
            default="text",
            help="Query type (default: text)",
        )
        query_parser.add_argument(
            "--attr", help="Attribute name (required for attribute type)"
        )

        # Set command
        set_parser = subparsers.add_parser("set", help="Set element value")
        set_parser.add_argument("xpath", help="XPath expression")
        set_parser.add_argument("value", help="New value")
        set_parser.add_argument(
            "--type",
            choices=["text", "attribute"],
            default="text",
            help="Set type (default: text)",
        )
        set_parser.add_argument(
            "--attr", help="Attribute name (required for attribute type)"
        )

        # Extract Data URI command
        extract_parser = subparsers.add_parser(
            "extract", help="Extract Data URI from element"
        )
        extract_parser.add_argument("xpath", help="XPath to element with Data URI")
        extract_parser.add_argument("--output", help="Save extracted data to file")
        extract_parser.add_argument(
            "--info", action="store_true", help="Show Data URI info only"
        )

        # List command
        list_parser = subparsers.add_parser("list", help="List elements")
        list_parser.add_argument(
            "--xpath", default="//*", help="XPath filter (default: //*)"
        )
        list_parser.add_argument(
            "--limit", type=int, default=20, help="Limit results (default: 20)"
        )

        # Add command
        add_parser = subparsers.add_parser("add", help="Add new element")
        add_parser.add_argument("parent_xpath", help="XPath to parent element")
        add_parser.add_argument("tag", help="New element tag name")
        add_parser.add_argument("--text", help="Element text content")
        add_parser.add_argument("--attrs", help="Attributes as key=value,key=value")

        # Remove command
        remove_parser = subparsers.add_parser("remove", help="Remove element")
        remove_parser.add_argument("xpath", help="XPath to element to remove")

        # Save command
        save_parser = subparsers.add_parser("save", help="Save file")
        save_parser.add_argument("--output", help="Output file path")
        save_parser.add_argument(
            "--backup", action="store_true", help="Create backup before saving"
        )

        # Info command
        info_parser = subparsers.add_parser("info", help="Show file information")

        # Shell command
        shell_parser = subparsers.add_parser("shell", help="Interactive shell mode")

        # Examples command
        examples_parser = subparsers.add_parser("examples", help="Create example files")
        examples_parser.add_argument(
            "--dir", default=".", help="Directory to create examples (default: .)"
        )

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        try:
            if args.command == "shell":
                self.start_shell()
            elif args.command == "examples":
                self.create_examples(args.dir)
            else:
                self.execute_command(args)
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def execute_command(self, args):
        """Execute a single command."""
        if args.command == "load":
            self.editor = FileEditor(args.file)
            file_type = "remote" if args.file.startswith("http") else "local"
            print(f"✅ Loaded {file_type} file: {args.file} ({self.editor.file_type})")

            info = self.editor.get_info()
            if "elements_count" in info:
                print(f"   Found {info['elements_count']} elements")

        elif args.command == "query":
            self._require_loaded_file()

            if args.type == "text":
                result = self.editor.get_element_text(args.xpath)
                print(f"Text: {result}")
            elif args.type == "attribute":
                if not args.attr:
                    print("❌ --attr required for attribute queries")
                    return
                result = self.editor.get_element_attribute(args.xpath, args.attr)
                print(f"Attribute {args.attr}: {result}")

        elif args.command == "extract":
            self._require_loaded_file()

            if args.info:
                # Show Data URI information only
                result = self.editor.extract_data_uri(args.xpath)
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print(f"✅ Data URI found:")
                    print(f"   MIME type: {result['mime_type']}")
                    print(f"   Encoding: {result['encoding']}")
                    print(f"   Size: {result['size']} bytes")
                    print(f"   Base64 length: {len(result['base64_data'])} chars")
            elif args.output:
                # Save to file
                success = self.editor.save_data_uri_to_file(args.xpath, args.output)
                if not success:
                    print("❌ Failed to extract and save Data URI")
            else:
                # Show raw data info
                result = self.editor.extract_data_uri(args.xpath)
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print(f"MIME: {result['mime_type']}")
                    print(f"Size: {result['size']} bytes")
                    preview = (
                        result["base64_data"][:100] + "..."
                        if len(result["base64_data"]) > 100
                        else result["base64_data"]
                    )
                    print(f"Base64 data: {preview}")

        elif args.command == "set":
            self._require_loaded_file()

            if args.type == "text":
                success = self.editor.set_element_text(args.xpath, args.value)
            elif args.type == "attribute":
                if not args.attr:
                    print("❌ --attr required for attribute updates")
                    return
                success = self.editor.set_element_attribute(
                    args.xpath, args.attr, args.value
                )

            if success:
                print("✅ Element updated")
            else:
                print("❌ Element not found")

        elif args.command == "list":
            self._require_loaded_file()

            elements = self.editor.list_elements(args.xpath)
            if not elements:
                print("No elements found")
                return

            print(f"Found {len(elements)} elements:")
            for i, elem in enumerate(elements[: args.limit]):
                print(f"\n{i + 1}. Path: {elem['path']}")
                print(f"   Tag: {elem['tag']}")
                if elem["text"]:
                    text_preview = (
                        elem["text"][:100] + "..."
                        if len(elem["text"]) > 100
                        else elem["text"]
                    )
                    print(f"   Text: {repr(text_preview)}")
                if elem["attributes"]:
                    print(f"   Attributes: {elem['attributes']}")

            if len(elements) > args.limit:
                print(
                    f"\n... and {len(elements) - args.limit} more (use --limit to see more)"
                )

        elif args.command == "add":
            self._require_loaded_file()

            # Parse attributes
            attributes = {}
            if args.attrs:
                for pair in args.attrs.split(","):
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        attributes[key.strip()] = value.strip()

            success = self.editor.add_element(
                args.parent_xpath, args.tag, args.text or "", attributes
            )
            if success:
                print("✅ Element added")
            else:
                print("❌ Parent element not found")

        elif args.command == "remove":
            self._require_loaded_file()

            success = self.editor.remove_element(args.xpath)
            if success:
                print("✅ Element removed")
            else:
                print("❌ Element not found")

        elif args.command == "info":
            self._require_loaded_file()

            info = self.editor.get_info()
            print("📄 File Information:")
            print(f"   Path: {info['file_path']}")
            print(f"   Type: {info['file_type']}")
            print(f"   Remote: {info['is_remote']}")
            print(f"   Size: {info['size']} bytes")
            if "elements_count" in info:
                print(f"   Elements: {info['elements_count']}")

        elif args.command == "save":
            self._require_loaded_file()

            if self.editor.is_remote and not args.output:
                print("❌ Remote file requires --output parameter")
                return

            if args.backup and not self.editor.is_remote:
                backup_path = self.editor.backup()
                print(f"📋 Backup created: {backup_path}")

            success = self.editor.save(args.output)
            if success:
                save_path = args.output or self.editor.file_path
                print(f"✅ File saved to {save_path}")
            else:
                print("❌ Save failed")

    def _require_loaded_file(self):
        """Check if a file is loaded, exit if not."""
        if not self.editor:
            print("❌ No file loaded. Use 'load' command first.")
            sys.exit(1)

    def start_shell(self):
        """Start interactive shell mode."""
        print("🚀 xsl Interactive Shell")
        print(f"Version: {__version__}")
        print("\nCommands:")
        print("  load <file>              - Load file (local path or URL)")
        print("  query <xpath>            - Query element text")
        print("  attr <xpath> <name>      - Get element attribute")
        print("  set <xpath> <value>      - Set element text")
        print("  setattr <xpath> <n> <v>  - Set element attribute")
        print("  extract <xpath>          - Show Data URI info")
        print("  save [path]              - Save file")
        print("  list [xpath]             - List elements")
        print("  info                     - Show file info")
        print("  help                     - Show this help")
        print("  exit                     - Exit shell")
        print()

        while True:
            try:
                command_line = input("xsl> ").strip()
                if not command_line:
                    continue

                if command_line == "exit":
                    break
                elif command_line == "help":
                    print(
                        "Available commands: load, query, attr, set, setattr, extract, save, list, info, help, exit"
                    )
                    continue

                parts = command_line.split()
                command = parts[0]

                if command == "load" and len(parts) == 2:
                    self.editor = FileEditor(parts[1])
                    file_type = "remote" if parts[1].startswith("http") else "local"
                    print(f"✅ Loaded {file_type} file ({self.editor.file_type})")

                elif command == "query" and len(parts) >= 2:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = " ".join(parts[1:])
                    result = self.editor.get_element_text(xpath)
                    print(f"Result: {result}")

                elif command == "attr" and len(parts) >= 3:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    attr_name = parts[2]
                    result = self.editor.get_element_attribute(xpath, attr_name)
                    print(f"Attribute {attr_name}: {result}")

                elif command == "set" and len(parts) >= 3:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    value = " ".join(parts[2:])
                    success = self.editor.set_element_text(xpath, value)
                    print("✅ Updated" if success else "❌ Not found")

                elif command == "setattr" and len(parts) >= 4:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1]
                    attr_name = parts[2]
                    attr_value = " ".join(parts[3:])
                    success = self.editor.set_element_attribute(
                        xpath, attr_name, attr_value
                    )
                    print("✅ Updated" if success else "❌ Not found")

                elif command == "extract" and len(parts) >= 2:
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = " ".join(parts[1:])
                    result = self.editor.extract_data_uri(xpath)
                    if "error" in result:
                        print(f"❌ {result['error']}")
                    else:
                        print(
                            f"✅ MIME: {result['mime_type']}, Size: {result['size']} bytes"
                        )

                elif command == "list":
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    xpath = parts[1] if len(parts) > 1 else "//*"
                    elements = self.editor.list_elements(xpath)[:10]  # limit to 10
                    for elem in elements:
                        text_preview = (
                            elem["text"][:50] + "..."
                            if len(elem["text"]) > 50
                            else elem["text"]
                        )
                        print(f"{elem['tag']}: {repr(text_preview)}")

                elif command == "info":
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    info = self.editor.get_info()
                    print(
                        f"File: {info['file_path']} ({info['file_type']}, {info['size']} bytes)"
                    )
                    if "elements_count" in info:
                        print(f"Elements: {info['elements_count']}")

                elif command == "save":
                    if not self.editor:
                        print("❌ No file loaded")
                        continue
                    output = parts[1] if len(parts) > 1 else None
                    if self.editor.is_remote and not output:
                        print("❌ Remote file requires output path")
                        continue
                    success = self.editor.save(output)
                    print("✅ Saved" if success else "❌ Save failed")

                else:
                    print(
                        "❌ Unknown command or wrong arguments. Type 'help' for available commands."
                    )

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def create_examples(self, directory: str):
        """Create example files for testing."""
        from .examples import create_example_files

        try:
            create_example_files(directory)
            print(f"✅ Example files created in {directory}")
        except Exception as e:
            print(f"❌ Error creating examples: {e}")


def main(args: List[str] = None) -> int:
    """Entry point for the xsl CLI command.
    
    Args:
        args: Command line arguments (default: None, uses sys.argv)
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    cli = CLI()
    try:
        cli.run(args)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
