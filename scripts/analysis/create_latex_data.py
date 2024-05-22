from analyze import Stats, DataStats, SchemaStats, ColumnStats, SchemaColumnStats
from pathlib import Path
import numpy as np
import plotly.express as px
import plotly.io as pio
import json

pio.kaleido.scope.mathjax = None


def write_overview_table(table_stats: list[Stats]):
    with open('data/overview_table.tex', 'w') as f:
        f.write("""\\begin{tabular}{|l|r|r|r|r|r|}
\\hline
\\multirowcell{2}{\\textbf{Origin \\& Table Name}} & 
\\multirowcell{2}{\\textbf{Rows}} & 
\\multicolumn{2}{c|}{\\textbf{Columns}} & 
\\multicolumn{2}{c|}{\\textbf{JSONL Size}} \\\\
\\cline{3-6}
& & \\multicolumn{1}{c|}{\\textbf{Nested}} & \\multicolumn{1}{c|}{\\textbf{Simple}} & 
\\multicolumn{1}{c|}{\\textbf{Plain}} & \\multicolumn{1}{c|}{\\textbf{Gzipped}} \\\\
""")
        for i in range(len(table_stats)):
            def get_size_str(size: int) -> str:
                match size:
                    case kb if kb < 1024:
                        return f"{kb:.2f} KB"
                    case kb if kb < 1024 * 1024:
                        return f"{kb / 1024:.2f} MB"
                    case kb:
                        return f"{kb / 1024 / 1024:.2f} GB"

            stat = table_stats[i]
            nested_cols = sum(stat.schema.nested_type_counts.values())
            simple_cols = sum(stat.schema.simple_type_counts.values())
            if i == len(table_stats) - 1:
                f.write(f"\\Xhline{{2.0pt}} \\textbf{{Total: {len(table_stats) - 1} Tables}} & "
                        f"\\textbf{{{stat.data.row_count:,}}} & "
                        f"\\textbf{{{nested_cols:,}}} & \\textbf{{{simple_cols:,}}} & "
                        f"\\textbf{{{get_size_str(stat.jsonl_kb)}}} & \\textbf{{{get_size_str(stat.jsonl_gz_kb)}}} "
                        f"\\\\\n")
            else:
                f.write(f"\\hline \\lstinline|{stat.dataset}-{stat.name}| & "
                        f"{stat.data.row_count:,} & {nested_cols:,} & {simple_cols:,} & "
                        f"{get_size_str(stat.jsonl_kb)} & {get_size_str(stat.jsonl_gz_kb)} \\\\\n")
        f.write("\\hline\n\\end{tabular}\n")


def plot_coltype_bar_chart(total_schema_stats: SchemaStats):
    type_counts = dict(total_schema_stats.nested_type_counts)
    type_counts.update(total_schema_stats.simple_type_counts)

    percents = [
        100 * v / sum(total_schema_stats.nested_type_counts.values()
                      if k in total_schema_stats.nested_type_counts
                      else total_schema_stats.simple_type_counts.values())
        for k, v in type_counts.items()]
    fig = px.bar(
        x=type_counts.keys(),
        y=type_counts.values(),
        text=[f"{p:1.1f}%" for p in percents],
        color=['Nested Type' if x in total_schema_stats.nested_type_counts
               else 'Simple Type' for x in type_counts.keys()],
        labels={'x': 'Column Type', 'y': 'Number of Columns', 'color': 'Type Category'},
        width=600,
        height=300
    )
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        font_family="Serif"
    )
    fig.update_traces(textangle=0)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.write_image(f'figures/coltype_bar_chart.pdf')


def plot_lengths_histogram_chart(all_col_stats: list[ColumnStats], types: set[str],
                                 type_str: str, trim: int, n_bins: int):
    list_stats = [col for col in all_col_stats if col.type in types and col.avg_length is not None]

    bins = np.append(np.linspace(0, trim, n_bins), np.inf)
    counts, bins = np.histogram([col.avg_length for col in list_stats], bins=bins)
    bins = [str(int(x)) for x in bins[:-1]]
    bins[-1] = f'{trim}+'

    fig = px.bar(
        x=bins,
        y=counts,
        labels={
            'x': f'Avg. {type_str} Length (max: {max([col.avg_length for col in list_stats]):.0f})',
            'y': 'Number of Columns'
        },
        width=200,
        height=300,
    )
    fig.update_xaxes(
        tickmode='linear',
        dtick=(n_bins - 1) // 10,
        titlefont=dict(size=11.5)
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        bargap=0,
        font_family="Serif"
    )
    fig.write_image(f'figures/lengths_histogram_{type_str}.pdf')


def plot_percentage_histogram_chart(col_stats: list[ColumnStats], field: str, name: str):
    col_stats = [getattr(x, f'{field}_percentage') for x in col_stats]

    counts, bins = np.histogram([col for col in col_stats if col is not None], bins=10)
    bins = [f'{int(x)}%' for x in bins[1:]]
    bins[0] = f'<{bins[0]}'

    fig = px.bar(
        x=bins,
        y=counts,
        labels={
            'x': f'Percentage of {field.capitalize()} Values',
            'y': 'Number of Columns'
        },
        width=200,
        height=300
    )
    fig.update_xaxes(titlefont=dict(size=11.5))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        bargap=0,
        font_family="Serif"
    )
    fig.write_image(f'figures/{field}_histogram_{name}.pdf')


def plot_depth_histogram_chart(all_col_stats: list[SchemaColumnStats], field: str, title: str, trim: int = None):
    data = [getattr(col, field) for col in all_col_stats]
    if trim is not None:
        bins = np.append(np.linspace(min(data), trim, trim + 1), np.inf)
    else:
        bins = range(min(data), max(data) + 2)
    counts, bins = np.histogram(data, bins=bins)
    bins = [str(int(x)) for x in bins[:-1]]
    if trim is not None:
        bins[-1] = f'{trim}+'

    fig = px.bar(
        x=bins,
        y=counts,
        labels={
            'x': title + (' (max: ' + str(max(data)) + ')' if trim is not None else ''),
            'y': 'Number of Columns'
        },
        width=200,
        height=300,
    )
    fig.update_xaxes(
        tickfont=dict(size=9)
    )
    if trim is not None:
        fig.update_xaxes(titlefont=dict(size=11.5))
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightPink')
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        bargap=0,
        font_family="Serif"
    )
    fig.write_image(f'figures/histogram_{field}.pdf')


def main():
    table_stats: list[Stats] = []
    with open('table_stats.json') as f:
        for stat in json.load(f):
            table_stats.append(Stats(**stat))
            table_stats[-1].data = DataStats(**table_stats[-1].data)
            table_stats[-1].data.col_stats = [ColumnStats(**col) for col in table_stats[-1].data.col_stats]
            table_stats[-1].schema = SchemaStats(**table_stats[-1].schema)
            table_stats[-1].schema.col_stats = [SchemaColumnStats(**col) for col in table_stats[-1].schema.col_stats]
            table_stats[-1].finalize()

    Path('data').mkdir(exist_ok=True)
    Path('figures').mkdir(exist_ok=True)

    write_overview_table(table_stats)

    plot_coltype_bar_chart(table_stats[-1].schema)

    plot_lengths_histogram_chart(table_stats[-1].data.col_stats, {'list', 'map'}, 'List', 20, 21)
    plot_lengths_histogram_chart(table_stats[-1].data.col_stats, {'varchar'}, 'String', 100, 11)

    nested_stats = [col for col in table_stats[-1].data.col_stats if col.type in {'list', 'map', 'struct'}]
    simple_stats = [col for col in table_stats[-1].data.col_stats if col.type not in {'list', 'map', 'struct'}]

    plot_percentage_histogram_chart(nested_stats, 'null', 'nested')
    plot_percentage_histogram_chart(simple_stats, 'null', 'simple')

    plot_percentage_histogram_chart(nested_stats, 'unique', 'nested')
    plot_percentage_histogram_chart(simple_stats, 'unique', 'simple')

    plot_depth_histogram_chart(table_stats[-1].schema.col_stats, 'depth', 'Column Depth')
    plot_depth_histogram_chart(table_stats[-1].schema.col_stats, 'list_depth', 'Column List-Only Depth')
    plot_depth_histogram_chart([x for x in table_stats[-1].schema.col_stats if x.type == 'struct'], 'simple_subfields',
                               'Simple Struct Subfields', 20)


if __name__ == "__main__":
    main()
