(* Bounded cross-tool reference. No production matrices, states or code are loaded. *)
ClearAll["Global`*"];
here = DirectoryName[$InputFileName];
output = Last[$ScriptCommandLine];
If[FileExistsQ[output], Print["Refusing to overwrite evidence"]; Exit[2]];
protocolFile = FileNameJoin[{here, "protocol-v1.json"}];
planFile = FileNameJoin[{here, "wolfram-plan-v1.json"}];
p = Import[protocolFile, "RawJSON"];
plan = Import[planFile, "RawJSON"];
exact[value_] := Rationalize[value, 10^-14];
machine[value_] := N[value, MachinePrecision];
complexJSON[value_] := <|"real" -> machine[Re[value]], "imag" -> machine[Im[value]]|>;
require[condition_, reason_] := If[!TrueQ[condition], Throw[reason, "referenceFailure"]];

assemble[level_, boundary_, length_] := Module[
  {cells = {{{0, 0}, {1, 0}, {0, 1}}}, scale = 1, vertices, ids, edges,
   adjacency, counts, weights, stiffness, corners, active},
  require[MemberQ[{0, 1, 2}, level] && MemberQ[{"neumann", "dirichlet"}, boundary] &&
    MemberQ[{3/4, 1, 5/2}, exact[length]] && !(level == 0 && boundary == "dirichlet"),
    "Graph case outside registered bounds"];
  Do[cells = Join @@ Table[Map[# + shift &, cells, {2}],
      {shift, {{0, 0}, {scale, 0}, {0, scale}}}]; scale *= 2, {level}];
  vertices = Union[Flatten[cells, 1]];
  ids = Map[First[FirstPosition[vertices, #]] &, cells, {2}];
  edges = Union[Sort /@ Flatten[Subsets[#, {2}] & /@ ids, 1]];
  adjacency = Normal[SparseArray[(# -> 1) & /@ Join[edges, Reverse /@ edges],
    {Length[vertices], Length[vertices]}]];
  counts = Counts[Flatten[ids]];
  weights = Table[counts[i]/3^(level + 1), {i, Length[vertices]}];
  stiffness = (5/3)^level/exact[length]^2 *
    (DiagonalMatrix[Total[adjacency]] - adjacency);
  corners = (First[FirstPosition[vertices, #]] &) /@ {{0, 0}, {scale, 0}, {0, scale}};
  active = If[boundary == "neumann", Range[Length[vertices]],
    Complement[Range[Length[vertices]], corners]];
  <|"vertices" -> vertices, "edges" -> edges - 1, "active" -> active - 1,
    "boundary_ids" -> corners - 1, "mass" -> weights[[active]],
    "stiffness" -> stiffness[[active, active]], "level" -> level|>
];

initialState[g_] := Module[{q, state},
  q = g["vertices"][[g["active"] + 1]]/2^g["level"];
  state = (1 + q[[All, 1]]/5 + q[[All, 2]]/10) *
    Exp[I*(2*q[[All, 1]]/5 - 3*q[[All, 2]]/10)];
  state/Sqrt[Total[g["mass"]*Abs[state]^2]]
];

fftCases[] := Module[{f = p["fft"], rows = {}, x, psi, energy, norm, shapes, modes},
  require[f["lengths"] == {0.75, 1., 2.5} && f["masses"] == {0.7, 1.7}, "FFT parameters changed"];
  Do[
    shapes = f["shapes_" <> ToString[dimension] <> "d"];
    modes = f["modes_" <> ToString[dimension] <> "d"];
    require[shapes == If[dimension == 3, {{8, 8, 8}, {16, 16, 16}, {8, 12, 10}},
      {{8, 8}, {16, 16}, {8, 12}}] && modes == If[dimension == 3,
      {{1, 0, 0}, {1, -2, 1}}, {{1, 0}, {1, -2}}], "FFT cases changed"];
    x = Table[Unique["x"], {dimension}];
    Do[
      psi = Exp[2*Pi*I*(mode.x)/exact[length]]/exact[length]^(dimension/2);
      energy = FullSimplify[-exact[length]^dimension*Conjugate[psi]*
        Total[Table[D[psi, {coordinate, 2}], {coordinate, x}]]/(2*exact[mass]),
        Element[x, Reals]];
      norm = FullSimplify[exact[length]^dimension*Conjugate[psi]*psi, Element[x, Reals]];
      AppendTo[rows, <|"backend" -> If[dimension == 3, "numpy", "numpy_fractal_ssfm"],
        "shape" -> shape, "length" -> length, "mass" -> mass, "mode" -> mode,
        "energy" -> machine[energy], "norm" -> machine[norm]|>],
      {shape, shapes}, {length, f["lengths"]}, {mass, f["masses"]}, {mode, modes}],
    {dimension, {3, 2}}]; rows
];

graphCases[] := Module[{rows = {}, g, values, vectors, order, weighted, groups,
  projectors, nominal, start, state, tail, gap = exact[p["graph"]["reference_cluster_relative_gap"]]},
  require[p["graph"]["levels"] == {0, 1, 2} &&
    p["graph"]["boundaries"] == {"neumann", "dirichlet"} &&
    p["graph"]["lengths"] == {0.75, 1., 2.5}, "Graph cases changed"];
  Do[If[!(level == 0 && boundary == "dirichlet"),
    g = assemble[level, boundary, length];
    {values, vectors} = Eigensystem[N[{g["stiffness"], DiagonalMatrix[g["mass"]]}, 60]];
    order = Ordering[values]; values = values[[order]]; vectors = vectors[[order]];
    weighted = (Sqrt[g["mass"]]*# &) /@ vectors;
    groups = Split[Range[Length[values]], Abs[values[[#2]] - values[[#1]]] <=
      gap*Max[1, Max[Abs[values]]] &];
    projectors = Table[With[{q = Orthogonalize[weighted[[group]]]},
      Transpose[q].Conjugate[q]], {group, groups}];
    nominal = Floor[exact[p["graph"]["tail_fraction"]]*Length[values]] + 1;
    start = First[First[Select[groups, MemberQ[#, nominal] &]]];
    state = N[Sqrt[g["mass"]]*initialState[g], 60];
    tail = Total[Pick[projectors, (First[#] >= start &) /@ groups]];
    AppendTo[rows, Join[g, <|"boundary" -> boundary, "length" -> length,
      "mass" -> machine[g["mass"]], "stiffness" -> machine[g["stiffness"]],
      "spectrum" -> machine[values], "groups" -> (groups - 1),
      "projectors" -> machine[projectors], "tail_start" -> start - 1,
      "initial" -> complexJSON[initialState[g]],
      "tail_power" -> machine[Re[Conjugate[state].tail.state/(Conjugate[state].state)]]|>]]],
    {level, p["graph"]["levels"]}, {boundary, p["graph"]["boundaries"]},
    {length, p["graph"]["lengths"]}]; rows
];

integrate[g_, initial_, potential_, gamma_, mass_, times_, precision_, goal_] := Module[
  {size = Length[initial], functions, x, y, h, v, c, rhs, equations, solutions, t},
  functions = Table[Unique["component"], {2*size}];
  x = Through[Take[functions, size][t]]; y = Through[Drop[functions, size][t]];
  h = N[DiagonalMatrix[1/g["mass"]].g["stiffness"]/(2*mass), precision];
  v = N[potential, precision]; c = N[gamma, precision];
  rhs = Join[h.y + (v + c*(x^2 + y^2))*y, -h.x - (v + c*(x^2 + y^2))*x];
  equations = Join[Thread[Through[(Derivative[1] /@ functions)[t]] == rhs],
    Thread[Through[functions[0]] == N[Join[Re[initial], Im[initial]], precision]]];
  solutions = NDSolveValue[equations, functions, {t, 0, Last[times]},
    WorkingPrecision -> precision, AccuracyGoal -> goal, PrecisionGoal -> goal,
    MaxStepSize -> Last[times]/64];
  require[ListQ[solutions] && Length[solutions] == 2*size &&
    And @@ (Head[#] === InterpolatingFunction & /@ solutions), "NDSolveValue failed"];
  Table[With[{values = Through[solutions[time]]},
    Take[values, size] + I*Drop[values, size]], {time, times}]
];

evolutionCases[] := Module[{e = p["evolution"], rows = {}, g, q, quadrants, potential,
  gamma, initial, times, references, agreement, h, linear},
  require[e["level"] == 2 && e["length"] == 1. && e["total_time"] == 0.01 &&
    e["step_counts"] == {4, 8, 16, 32} && e["boundaries"] == {"dirichlet", "neumann"} &&
    plan["working_precisions"] == {40, 60} && plan["accuracy_precision_goals"] == {20, 30},
    "Evolution cases or precision plan changed"];
  times = Range[0, 32]*exact[e["total_time"]]/32;
  Do[
    g = assemble[e["level"], boundary, e["length"]];
    q = g["vertices"][[g["active"] + 1]];
    quadrants = (If[3*#[[2]] >= 2^e["level"],
      If[2*#[[1]] + #[[2]] >= 2^e["level"], 1, 2],
      If[2*#[[1]] + #[[2]] >= 2^e["level"], 4, 3]] &) /@ q;
    potential = exact[e["quadrant_potential"]][[quadrants]];
    gamma = exact[e["coupling"]]*exact[e["quadrant_gamma"]][[quadrants]];
    initial = initialState[g];
    references = MapThread[integrate[g, initial, potential, gamma, exact[e["mass"]],
      times, #1, #2] &, {plan["working_precisions"], plan["accuracy_precision_goals"]}];
    agreement = Max[Sqrt[Total[g["mass"]*Abs[#]^2]] & /@ (references[[1]] - references[[2]])]/
      Sqrt[Total[g["mass"]*Abs[initial]^2]];
    h = DiagonalMatrix[1/g["mass"]].g["stiffness"]/(2*exact[e["mass"]]);
    linear = MatrixExp[N[-I*Last[times]*h, 60]].N[initial, 60];
    AppendTo[rows, <|"boundary" -> boundary, "mass" -> machine[g["mass"]],
      "stiffness" -> machine[g["stiffness"]], "times" -> machine[times],
      "potential" -> machine[potential], "gamma" -> machine[gamma],
      "initial" -> complexJSON[initial], "linear" -> complexJSON[linear],
      "reference_loose" -> complexJSON[references[[1]]],
      "reference" -> complexJSON[references[[2]]],
      "internal_precision_refinement_error" -> machine[agreement]|>],
    {boundary, e["boundaries"]}]; rows
];

started = AbsoluteTime[];
result = Catch[TimeConstrained[MemoryConstrained[
  <|"fft" -> fftCases[], "graph" -> graphCases[], "evolution" -> evolutionCases[]|>,
  536870912, "Memory limit exceeded"], 120, "Time limit exceeded"], "referenceFailure"];
receipt = <|"assessment_id" -> plan["assessment_id"], "source_commit" -> p["source_commit"],
  "status" -> If[AssociationQ[result], "EXECUTED", "INCONCLUSIVE"],
  "kernel_version" -> $Version, "system_id" -> $SystemID,
  "created_utc" -> DateString[TimeZoneConvert[Now, 0], "ISODateTime"],
  "elapsed_seconds" -> machine[AbsoluteTime[] - started],
  "protocol_file_sha256" -> FileHash[protocolFile, "SHA256", "HexString"],
  "plan_file_sha256" -> FileHash[planFile, "SHA256", "HexString"],
  "reference_file_sha256" -> FileHash[$InputFileName, "SHA256", "HexString"],
  "working_precisions" -> plan["working_precisions"],
  "scientific_validation_status" -> "NOT_ESTABLISHED", "human_disposition" -> "PENDING",
  "exercises" -> If[AssociationQ[result], result, <||>],
  "failure_reason" -> If[AssociationQ[result], Null, ToString[result, InputForm]]|>;
If[Export[output, receipt, "RawJSON"] === $Failed, Exit[2]];
Print[receipt["status"], " in ", receipt["elapsed_seconds"], " seconds"];
Exit[If[receipt["status"] == "EXECUTED", 0, 1]];
