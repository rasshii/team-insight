"use client";

import * as d3 from "d3";
import React from "react";

interface ThroughputData {
  date: string;
  completed: number;
}

interface ThroughputChartProps {
  data: ThroughputData[];
}

export function ThroughputChart({ data }: ThroughputChartProps) {
  const chartRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!chartRef.current || !data.length) return;

    // チャートの設定
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = chartRef.current.clientWidth - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // SVGの作成
    const svg = d3
      .select(chartRef.current)
      .append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // X軸のスケール
    const x = d3
      .scaleBand()
      .domain(data.map((d) => d.date))
      .range([0, width])
      .padding(0.1);

    // Y軸のスケール
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.completed) || 0])
      .range([height, 0]);

    // X軸の描画
    svg
      .append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end");

    // Y軸の描画
    svg.append("g").call(d3.axisLeft(y));

    // 線の生成
    const line = d3
      .line<ThroughputData>()
      .x((d) => (x(d.date) || 0) + x.bandwidth() / 2)
      .y((d) => y(d.completed));

    // 線の描画
    svg
      .append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#3b82f6")
      .attr("stroke-width", 2)
      .attr("d", line);

    // データポイントの描画
    svg
      .selectAll("circle")
      .data(data)
      .enter()
      .append("circle")
      .attr("cx", (d) => (x(d.date) || 0) + x.bandwidth() / 2)
      .attr("cy", (d) => y(d.completed))
      .attr("r", 4)
      .attr("fill", "#3b82f6")
      .on("mouseover", function (event, d) {
        d3.select(this).attr("r", 6).attr("fill", "#2563eb");
        // ツールチップの表示
        const tooltip = d3
          .select(chartRef.current)
          .append("div")
          .attr("class", "tooltip")
          .style("position", "absolute")
          .style("background", "white")
          .style("padding", "8px")
          .style("border-radius", "4px")
          .style("box-shadow", "0 2px 4px rgba(0,0,0,0.1)")
          .style("pointer-events", "none")
          .html(`<strong>${d.date}</strong><br/>完了: ${d.completed}件`)
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 10}px`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("r", 4).attr("fill", "#3b82f6");
        d3.selectAll(".tooltip").remove();
      });

    // クリーンアップ関数
    return () => {
      d3.select(chartRef.current).selectAll("*").remove();
    };
  }, [data]);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        スループット推移
      </h3>
      <div ref={chartRef} className="w-full" />
    </div>
  );
}
