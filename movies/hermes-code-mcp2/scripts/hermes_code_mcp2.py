from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
DIM = "#888888"
MONO = "Menlo"


class HermesCodeIntro(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("Hermes Code", font_size=52, color=PRIMARY, weight=BOLD, font=MONO)
        subtitle = Text(
            "bounded sovereign local-first runtime",
            font_size=26,
            color=DIM,
            font=MONO,
        )
        subtitle.next_to(title, DOWN, buff=0.4)

        self.play(Write(title), run_time=1.6)
        self.play(FadeIn(subtitle, shift=DOWN), run_time=1.0)
        self.wait(2.0)
        self.play(FadeOut(Group(title, subtitle)), run_time=0.6)


class VictusLocalRoot(Scene):
    def construct(self):
        self.camera.background_color = BG

        host = Text("Victus", font_size=48, color=PRIMARY, weight=BOLD, font=MONO)
        surface = Text("local context root", font_size=26, color=SECONDARY, font=MONO)
        addr = Text("pc://mesh/victus/local", font_size=22, color=ACCENT, font=MONO)

        group = Group(host, surface, addr).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        box = SurroundingRectangle(group, color=PRIMARY, buff=0.5, corner_radius=0.15)

        self.play(Create(box), run_time=1.2)
        self.play(FadeIn(group, shift=RIGHT), run_time=1.2)
        self.wait(1.8)
        self.play(FadeOut(Group(box, group)), run_time=0.6)


class ConductorDispatch(Scene):
    def construct(self):
        self.camera.background_color = BG

        cmd = Text("sim://250000", font_size=36, color=ACCENT, font=MONO)
        arrow = Arrow(start=LEFT, end=RIGHT, color=PRIMARY)
        surface = Text("surface: omniverse_simulation", font_size=24, color=SECONDARY, font=MONO)
        mech = Text("mech_lang: mech-sim/omniverse://sim/250000", font_size=20, color=DIM, font=MONO)

        row = Group(cmd, arrow, surface).arrange(RIGHT, buff=0.8)
        mech.next_to(row, DOWN, buff=0.6, aligned_edge=LEFT)

        self.play(Write(cmd), run_time=1.2)
        self.play(GrowArrow(arrow), run_time=0.8)
        self.play(FadeIn(surface, shift=UP), run_time=0.9)
        self.play(FadeIn(mech, shift=UP), run_time=0.9)
        self.wait(1.8)
        self.play(FadeOut(Group(row, mech)), run_time=0.6)


class MCP2Mesh(Scene):
    def construct(self):
        self.camera.background_color = BG

        client = Text("MCP client", font_size=32, color=PRIMARY, font=MONO)
        bridge = Text("/mcp/tools", font_size=32, color=ACCENT, font=MONO)
        conductor = Text("Hermes conductor", font_size=32, color=SECONDARY, font=MONO)

        stack = Group(client, bridge, conductor).arrange(DOWN, buff=0.7)
        arrows = VGroup()
        for a, b in zip([client, bridge], [bridge, conductor]):
            arrows.add(Arrow(start=a.get_bottom(), end=b.get_top(), color=DIM, buff=0.15))

        top_label = Text("Victus virtual mesh node", font_size=22, color=DIM, font=MONO)
        top_label.next_to(stack, UP, buff=0.5)

        self.play(FadeIn(top_label, shift=DOWN), run_time=0.9)
        self.play(FadeIn(stack, shift=RIGHT), run_time=1.3)
        self.play(Create(arrows), run_time=1.2)
        self.wait(2.0)
        self.play(FadeOut(Group(top_label, stack, arrows)), run_time=0.6)


class LocalTokenProof(Scene):
    def construct(self):
        self.camera.background_color = BG

        token_src = Text("local model token", font_size=30, color=PRIMARY, font=MONO)
        token_sink = Text("pc://local/token sim", font_size=30, color=ACCENT, font=MONO)
        result = Text("sim://250000 + mech_lang token", font_size=24, color=SECONDARY, font=MONO)

        group = Group(token_src, token_sink, result).arrange(DOWN, buff=0.6)
        box = SurroundingRectangle(group, color=ACCENT, buff=0.5, corner_radius=0.15)

        self.play(Create(box), run_time=1.2)
        self.play(FadeIn(group, shift=RIGHT), run_time=1.2)
        self.wait(1.8)
        self.play(FadeOut(Group(box, group)), run_time=0.6)


class Closing(Scene):
    def construct(self):
        self.camera.background_color = BG

        line1 = Text("Command and control surface", font_size=36, color=PRIMARY, font=MONO)
        line2 = Text("Hermes conductor", font_size=28, color=SECONDARY, font=MONO)
        line3 = Text("MCP2", font_size=24, color=ACCENT, font=MONO)

        group = Group(line1, line2, line3).arrange(DOWN, buff=0.5)
        self.play(FadeIn(line1, shift=UP), run_time=0.9)
        self.play(FadeIn(line2, shift=UP), run_time=0.9)
        self.play(FadeIn(line3, shift=UP), run_time=0.8)
        self.wait(2.0)
        self.play(FadeOut(Group(line1, line2, line3)), run_time=0.7)
