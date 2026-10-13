module comparator #(
    parameter int WIDTH = 2
) (
    input  bit             clk,
    input  bit             rst_n,
    input  bit [WIDTH-1:0] a,
    input  bit [WIDTH-1:0] b,
    output logic             eq,
    output logic             gt,
    output logic             lt
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            eq <= 1'b0;
            gt <= 1'b0;
            lt <= 1'b0;
        end else begin
            eq <= (a == b);
            gt <= (a > b);
            lt <= (a < b);
        end
    end
endmodule
