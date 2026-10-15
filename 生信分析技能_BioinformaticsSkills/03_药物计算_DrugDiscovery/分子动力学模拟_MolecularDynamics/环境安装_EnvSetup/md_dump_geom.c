#include <origin.h>
#pragma labtalk(1)

static FILE* g_fp = NULL;

static void step(const char* s)
{
    if (g_fp)
    {
        fprintf(g_fp, "STEP %s\n", s);
        fflush(g_fp);
    }
}

static void dump_node(TreeNode tr, string& path, int depth)
{
    if (depth > 10)
        return;
    TreeNode nn = tr.FirstNode;
    while (nn)
    {
        string tag = nn.tagName;
        fprintf(g_fp, "NODE d=%d [%s]\n", depth, tag.GetBuffer(0));
        tag.ReleaseBuffer();
        fflush(g_fp);
        if (nn.FirstNode)
            dump_node(nn, path, depth + 1);
        nn = nn.NextNode;
    }
}

void md_try_spectrum()
{
    FILE* fp = fopen("E:\\Origin_Data\\_probe\\oc_spec.txt", "w");
    if (!fp)
        return;
    fprintf(fp, "open\n");
    fflush(fp);
    GraphLayer gl = Project.ActiveLayer();
    GraphObject go = gl.GraphObjects("SPECTRUM1");
    fprintf(fp, "got\n");
    fflush(fp);
    string nm = go.GetName();
    fprintf(fp, "name=[%s] L=%d T=%d W=%d H=%d\n", nm.GetBuffer(0), go.Left, go.Top, go.Width, go.Height);
    nm.ReleaseBuffer();
    fflush(fp);
    string tx = go.Text;
    fprintf(fp, "text=[%s]\n", tx.GetBuffer(0));
    tx.ReleaseBuffer();
    fflush(fp);
    fclose(fp);
}

void md_verify_fit()
{
    FILE* fp = fopen("E:\\Origin_Data\\_verify_log.txt", "a");
    LT_execute("vVPW = page.width; vVPH = page.height;");
    double pw = 0, ph = 0;
    LT_get_var("vVPW", &pw);
    LT_get_var("vVPH", &ph);
    GraphLayer gl = Project.ActiveLayer();
    RECT fr;
    fr.left = 0; fr.top = 0; fr.right = 0; fr.bottom = 0;
    gl.GetAllLinkedLayersFrame(fr);
    double L = fr.left, T = fr.top, R = fr.right, B = fr.bottom;
    int nobj = gl.GraphObjects.Count();
    for (int i = 0; i < nobj && i < 80; i++)
    {
        GraphObject go = gl.GraphObjects(i);
        string nm = go.GetName();
        char* pnm = nm.GetBuffer(0);
        bool skip = (pnm[0] == '_');
        nm.ReleaseBuffer();
        if (skip)
            continue;
        int w = go.Width;
        int h = go.Height;
        if (w <= 0 || h <= 0)
            continue;
        if (go.Left < L)
            L = go.Left;
        if (go.Top < T)
            T = go.Top;
        if (go.Left + w > R)
            R = go.Left + w;
        if (go.Top + h > B)
            B = go.Top + h;
    }
    int ok = (L >= 0 && T >= 0 && R <= pw && B <= ph) ? 1 : 0;
    LT_set_var("vMdVerifyOK", ok);
    if (fp)
    {
        fprintf(fp, "VERIFY ok=%d page=%.0fx%.0f bbox=L%.0f T%.0f R%.0f B%.0f\n",
                ok, pw, ph, L, T, R, B);
        fclose(fp);
    }
    if (!ok)
        LT_execute("exit;");
}

void md_probe_tree()
{
    FILE* fp = fopen("E:\\Origin_Data\\_probe\\oc_t2.txt", "w");
    if (!fp)
        return;
    fprintf(fp, "open\n");
    fflush(fp);
    GraphLayer gl = Project.ActiveLayer();
    fprintf(fp, "layer\n");
    fflush(fp);
    DataPlot dp = gl.DataPlots(0);
    fprintf(fp, "dp\n");
    fflush(fp);
    Tree trf;
    trf = dp.GetFormat(FPB_ALL, FOB_ALL, true, true);
    fprintf(fp, "tree\n");
    fflush(fp);
    TreeNode nn = trf.Root.FirstNode;
    fprintf(fp, "first\n");
    fflush(fp);
    int cnt = 0;
    while (nn && cnt < 300)
    {
        string tag = nn.tagName;
        fprintf(fp, "NODE [%s]\n", tag.GetBuffer(0));
        tag.ReleaseBuffer();
        fflush(fp);
        nn = nn.NextNode;
        cnt++;
    }
    fprintf(fp, "walk done %d\n", cnt);
    fflush(fp);
    fclose(fp);
}

void md_dump_geom()
{
    g_fp = fopen("E:\\Origin_Data\\_probe\\oc_dump.txt", "w");
    if (!g_fp)
    {
        LT_set_var("vDumpOK", -1);
        return;
    }
    step("fopen");

    LT_execute("vTmpPW = page.width; vTmpPH = page.height;");
    double pw = 0, ph = 0;
    LT_get_var("vTmpPW", &pw);
    LT_get_var("vTmpPH", &ph);
    fprintf(g_fp, "PAGE %.4f %.4f\n", pw, ph);
    step("lt_vars");

    GraphLayer gl = Project.ActiveLayer();
    step("active_layer");

    double pos[4];
    pos[0] = 0; pos[1] = 0; pos[2] = 0; pos[3] = 0;
    int ngp = gl.GetPosition(pos);
    fprintf(g_fp, "LAYER_POS ret=%d %.4f %.4f %.4f %.4f\n", ngp, pos[0], pos[1], pos[2], pos[3]);
    step("layer_pos");

    RECT rc;
    rc.left = 0; rc.top = 0; rc.right = 0; rc.bottom = 0;
    int okf = gl.GetAllLinkedLayersFrame(rc);
    fprintf(g_fp, "LAYERS_FRAME ok=%d %ld %ld %ld %ld\n", okf, rc.left, rc.top, rc.right, rc.bottom);
    step("layers_frame");

    int nobj = gl.GraphObjects.Count();
    fprintf(g_fp, "NOBJ %d\n", nobj);
    step("nobj");
    for (int i = 0; i < nobj && i < 60; i++)
    {
        GraphObject go = gl.GraphObjects(i);
        string nm = go.GetName();
        int w = go.Width;
        int h = go.Height;
        fprintf(g_fp, "OBJ %d name=[%s] L=%d T=%d W=%d H=%d X=%.3f Y=%.3f dX=%.3f dY=%.3f",
                i, nm.GetBuffer(0), go.Left, go.Top, w, h, go.X, go.Y, go.DX, go.DY);
        nm.ReleaseBuffer();
        fflush(g_fp);
        bool bTryText = false;
        {
            char* pnm = nm.GetBuffer(0);
            if ((pnm[0] == 'X' && pnm[1] == 'B') || (pnm[0] == 'Y' && pnm[1] == 'L') ||
                (pnm[0] == 'Y' && pnm[1] == 'R') || (pnm[0] == 'X' && pnm[1] == 'T') ||
                (pnm[0] == 'S' && pnm[1] == 'P'))
                bTryText = true;
            nm.ReleaseBuffer();
        }
        if (w > 0 && h > 0 && bTryText)
        {
            string tx = go.Text;
            fprintf(g_fp, " text=[%s]", tx.GetBuffer(0));
            tx.ReleaseBuffer();
            fflush(g_fp);
        }
        fprintf(g_fp, "\n");
        fflush(g_fp);
    }
    step("objs_done");

    fclose(g_fp);
    g_fp = NULL;
    LT_set_var("vDumpOK", 1);
}

void md_dump_tree()
{
    g_fp = fopen("E:\\Origin_Data\\_probe\\oc_tree.txt", "w");
    if (!g_fp)
    {
        LT_set_var("vDumpOK", -2);
        return;
    }
    step("tree_fopen");
    GraphLayer gl = Project.ActiveLayer();
    step("tree_layer");
    int np = gl.DataPlots.Count();
    fprintf(g_fp, "NDP %d\n", np);
    step("tree_ndp");
    for (int i = 0; i < np && i < 4; i++)
    {
        DataPlot dp = gl.DataPlots(i);
        step("tree_dp_acquired");
        Tree trf;
        trf = dp.GetFormat(FPB_ALL, FOB_ALL, true, true);
        step("tree_got_format");
        fprintf(g_fp, "=== DP %d TREE\n", i);
        fflush(g_fp);
        string rootPath("R");
        dump_node(trf.Root, rootPath, 0);
        step("tree_dp_done");
    }
    fclose(g_fp);
    g_fp = NULL;
    LT_set_var("vDumpOK", 2);
}
