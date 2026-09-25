import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from prepare_data import CLEAN_PATH, METHOD_ORDER, NEAR_PC, ROOT, SURVEY_ORDER

FIG_DIR = ROOT / "figures"

METHOD_COLORS = {
    "Transit": "#0072B2",
    "Radial Velocity": "#E69F00",
    "Microlensing": "#CC79A7",
    "Imaging": "#009E73",
    "Other": "#999999",
}

SURVEY_COLORS = {
    "Kepler": "#D55E00",
    "K2": "#E69F00",
    "TESS": "#0072B2",
    "Radial Velocity": "#009E73",
    "Microlensing": "#CC79A7",
    "Imaging": "#56B4E9",
    "Other transit": "#882255",
    "Other": "#999999",
}


def load():
    df = pd.read_csv(CLEAN_PATH)
    df["method"] = pd.Categorical(df["method"], METHOD_ORDER, ordered=True)
    df["survey"] = pd.Categorical(df["survey"], SURVEY_ORDER, ordered=True)
    return df


def save_timeline(df):
    counts = (
        df.groupby(["disc_year", "method"], observed=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=METHOD_ORDER)
    )
    years = counts.index.astype(int)

    fig, ax = plt.subplots(figsize=(12.5, 6.2), dpi=140)
    bottom = np.zeros(len(counts))
    for method in METHOD_ORDER:
        values = counts[method].to_numpy()
        ax.bar(years, values, bottom=bottom, width=0.85, color=METHOD_COLORS[method], label=method)
        bottom += values
    ax.set_title("Transit surveys take over the catalog after Kepler", loc="left", fontsize=16, pad=12)
    ax.set_xlabel("Discovery year", fontsize=13)
    ax.set_ylabel("Confirmed planets published that year", fontsize=13)
    ax.tick_params(labelsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=11, ncol=5, loc="upper left")
    ax.set_xlim(years.min() - 0.6, years.max() + 0.6)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_discoveries_by_method.png")
    plt.close(fig)

    bars = []
    for method in METHOD_ORDER:
        bars.append(
            go.Bar(
                x=years,
                y=counts[method],
                name=method,
                marker_color=METHOD_COLORS[method],
                hovertemplate="%{x}: %{y} " + method + " planets<extra></extra>",
            )
        )
    fig_w = go.Figure(bars)
    fig_w.update_layout(
        barmode="stack",
        template="plotly_white",
        title="Transit surveys take over the catalog after Kepler",
        xaxis_title="Discovery year",
        yaxis_title="Confirmed planets published that year",
        legend_title="Discovery method",
        font=dict(size=16),
        width=1200,
        height=640,
        margin=dict(l=70, r=30, t=70, b=60),
    )
    fig_w.write_html(FIG_DIR / "01_discoveries_by_method.html")


def survey_traces(part, show_legend):
    traces = []
    for survey in SURVEY_ORDER:
        rows = part[part["survey"] == survey]
        traces.append(
            go.Scatter3d(
                x=rows["x_pc"],
                y=rows["y_pc"],
                z=rows["z_pc"],
                mode="markers",
                name=survey,
                legendgroup=survey,
                showlegend=show_legend,
                marker=dict(size=2.4, color=SURVEY_COLORS[survey], opacity=0.82),
                customdata=np.stack(
                    [
                        rows["pl_name"],
                        rows["disc_year"].astype(int),
                        rows["sy_dist"].round(1),
                        rows["discoverymethod"],
                    ],
                    axis=1,
                ),
                hovertemplate=(
                    "%{customdata[0]}<br>Year %{customdata[1]}"
                    "<br>%{customdata[3]}<br>%{customdata[2]} pc<extra>" + survey + "</extra>"
                ),
            )
        )
    return traces


def save_cone(df):
    near = df[df["within_2000_pc"]].copy()
    years = list(range(2008, int(df["disc_year"].max()) + 1))
    axis = dict(
        title_font=dict(size=14),
        tickfont=dict(size=11),
        range=[-NEAR_PC, NEAR_PC],
        backgroundcolor="#f7f7f7",
        gridcolor="#dddddd",
        zerolinecolor="#888888",
    )

    first = near[near["disc_year"] <= years[0]]
    frames = []
    for year in years:
        seen = near[near["disc_year"] <= year]
        if year == years[0]:
            label = f"Through {year}, before Kepler"
        else:
            label = f"Through {year}"
        frames.append(
            go.Frame(
                name=str(year),
                data=survey_traces(seen, False),
                layout=go.Layout(title=dict(text=f"Confirmed planets within 2,000 pc. {label}")),
            )
        )

    fig = go.Figure(data=survey_traces(first, True), frames=frames)
    sliders = [
        dict(
            active=0,
            pad=dict(t=8),
            currentvalue=dict(prefix="Discovery year <= ", font=dict(size=16)),
            steps=[
                dict(
                    method="animate",
                    args=[[str(year)], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                    label=str(year),
                )
                for year in years
            ],
        )
    ]
    fig.update_layout(
        template="plotly_white",
        title=f"Confirmed planets within 2,000 pc. Through {years[0]}, before Kepler",
        font=dict(size=15),
        legend_title="Survey",
        width=1200,
        height=760,
        margin=dict(l=10, r=10, t=70, b=10),
        scene=dict(
            xaxis=dict(title="X (parsecs)", **axis),
            yaxis=dict(title="Y (parsecs)", **axis),
            zaxis=dict(title="Z (parsecs)", **axis),
            aspectmode="cube",
            camera=dict(eye=dict(x=1.45, y=1.15, z=0.55)),
        ),
        sliders=sliders,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.02,
                y=0.02,
                buttons=[
                    dict(
                        label="Play",
                        method="animate",
                        args=[None, dict(frame=dict(duration=450, redraw=True), fromcurrent=True)],
                    ),
                    dict(
                        label="Pause",
                        method="animate",
                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                    ),
                ],
            )
        ],
    )
    fig.write_html(FIG_DIR / "02_discovery_cone.html")

    ticks = [-2000, 0, 2000]
    fig_m = plt.figure(figsize=(11, 8.4), dpi=140)
    ax = fig_m.add_subplot(111, projection="3d")
    for survey in SURVEY_ORDER:
        rows = near[near["survey"] == survey]
        if rows.empty:
            continue
        ax.scatter(
            rows["x_pc"],
            rows["y_pc"],
            rows["z_pc"],
            s=6,
            c=SURVEY_COLORS[survey],
            label=survey,
            alpha=0.75,
            depthshade=False,
        )
    ax.set_xlim(-NEAR_PC, NEAR_PC)
    ax.set_ylim(-NEAR_PC, NEAR_PC)
    ax.set_zlim(-NEAR_PC, NEAR_PC)
    ax.view_init(elev=16, azim=-40)
    end_blank = plt.FuncFormatter(lambda v, pos: "" if abs(v) > 1500 else f"{int(v)}")
    ax.xaxis.set_major_formatter(end_blank)
    ax.yaxis.set_major_formatter(end_blank)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_zticks(ticks)
    ax.tick_params(labelsize=9, pad=2)
    ax.set_xlabel("X (parsecs)", fontsize=11, labelpad=12)
    ax.set_ylabel("Y (parsecs)", fontsize=11, labelpad=12)
    ax.set_zlabel("Z (parsecs)", fontsize=11, labelpad=10)
    ax.set_title("Confirmed planets within 2,000 pc of Earth", loc="left", fontsize=15, pad=8)
    ax.legend(loc="upper left", fontsize=9, frameon=False, markerscale=3)
    fig_m.subplots_adjust(left=0.0, right=0.98, bottom=0.04, top=0.92)
    fig_m.savefig(FIG_DIR / "02_discovery_cone_final.png")
    plt.close(fig_m)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = load()
    save_timeline(df)
    save_cone(df)
    print(f"figures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
