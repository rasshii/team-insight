"use client";

import * as d3 from "d3";
import React from "react";

interface BottleneckData {
  status: string;
  averageDays: number;
  ticketCount: number;
}

interface BottleneckChartProps {
  data: BottleneckData[];
}

export function BottleneckChart({ data }: BottleneckChartProps) {
  const chartRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!chartRef.current || !data.length) return;

    // チャートの設定
    const margin = { top: 20, right: 30, bottom: 40, left: 90 };
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
      .scaleLinear()
      .domain([0, d3.max(data, (d) => d.averageDays) || 0])
      .range([0, width]);

    // Y軸のスケール
    const y = d3
      .scaleBand()
      .domain(data.map((d) => d.status))
      .range([0, height])
      .padding(0.1);

    // X軸の描画
    svg
      .append("g")
      .attr("transform", `translate(0,${height})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(5)
          .tickFormat((d) => `${d}日`)
      );

    // Y軸の描画
    svg.append("g").call(d3.axisLeft(y));

    // バーの描画
    svg
      .selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
      .attr("x", 0)
      .attr("y", (d) => y(d.status) || 0)
      .attr("width", (d) => x(d.averageDays))
      .attr("height", y.bandwidth())
      .attr("fill", "#3b82f6")
      .attr("rx", 4)
      .attr("ry", 4)
      .on("mouseover", function (event, d) {
        d3.select(this).attr("fill", "#2563eb");
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
          .html(
            `<strong>${d.status}</strong><br/>平均: ${d.averageDays.toFixed(
              1
            )}日<br/>チケット数: ${d.ticketCount}件`
          )
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 10}px`);
      })
      .on("mouseout", function () {
        d3.select(this).attr("fill", "#3b82f6");
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
        ボトルネック分析
      </h3>
      <div ref={chartRef} className="w-full" />
    </div>
  );
}
