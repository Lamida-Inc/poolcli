import click
from rich.console import Console
from rich.text import Text
from rich.tree import Tree


class RecursiveHelpGroup(click.Group):
    """
    A Click command group that recursively prints help for all subcommands,
    showing nested structure with color and Rich formatting.
    """

    def format_help(self, ctx, formatter):
        console = Console()
        console.print("\n[bold blue]🌊 poolcli: A CLI for managing Bittensor subnet pool operations.")
        print("Usage: poolcli [global options/commands] [sub commands] [options]\n")
        root_tree = Tree("🌊 [bold cyan]poolcli[/bold cyan]")
        seen = set()
        self._build_rich_tree(ctx, group=self, tree=root_tree, seen=seen)

        options_tree = root_tree.add("[bold magenta]Global Options[/bold magenta]")
        for opt in ctx.command.get_params(ctx):
            if isinstance(opt, click.Option):
                opt_names = ", ".join(opt.opts + opt.secondary_opts)
                help_text = opt.help or ""
                opt_node = Text(opt_names, style="magenta")
                if help_text:
                    opt_node.append(f"  {help_text}", style="dim")
                options_tree.add(opt_node)

        console.print(root_tree)

    def _build_rich_tree(self, ctx, group, tree, seen):
        """
        Recursively build a rich Tree of all commands and their options.
        """
        for name in group.list_commands(ctx):
            cmd = group.get_command(ctx, name)
            if cmd is None or id(cmd) in seen:
                continue
            seen.add(id(cmd))

            if isinstance(cmd, click.Group):
                node_label = Text(f"{name}", style="bold green")
            else:
                node_label = Text(f"{name}", style="bold cyan")

            short_help = cmd.get_short_help_str(limit=60) or ""
            if short_help:
                node_label.append(f" — {short_help}", style="dim")

            cmd_branch = tree.add(node_label)

            options = [p for p in cmd.params if isinstance(p, click.Option)]
            for opt in options:
                opt_names = ", ".join(opt.opts + opt.secondary_opts)
                help_text = opt.help or ""
                opt_node = Text(opt_names, style="yellow")
                if help_text:
                    opt_node.append(f"  {help_text}", style="dim")
                cmd_branch.add(opt_node)

            if isinstance(cmd, click.Group):
                self._build_rich_tree(ctx, cmd, cmd_branch, seen)
