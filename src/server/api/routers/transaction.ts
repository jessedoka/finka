import { z } from "zod";

import { createTRPCRouter, publicProcedure } from "~/server/api/trpc";

export const transactionRouter = createTRPCRouter({
    create: publicProcedure
        .input(z.object({ memo: z.string().min(1), amount: z.number(), accountId: z.number() }))
        .mutation(async ({ ctx, input }) => {
        // simulate a slow db call
        await new Promise((resolve) => setTimeout(resolve, 1000));
    
        return ctx.db.transactions.create({
            data: {
                memo: input.memo,
                amount: input.amount,
                accountId: input.accountId,
                transactionDate: new Date() // Add the transactionDate property
            },
        });
    }),

    getLatest: publicProcedure.query(({ ctx }) => {
        return ctx.db.transactions.findFirst({
            orderBy: {
                createdAt: "desc",
            },
        });
    }),

    getAll: publicProcedure.query(({ ctx }) => {
        return ctx.db.transactions.findMany();
    }),

    getById: publicProcedure
        .input(z.object({ id: z.number().optional() }))
        .query(({ ctx, input }) => {
        return ctx.db.transactions.findUnique({
            where: {
                id: input.id,
            },
        });
    }),

    update: publicProcedure
        .input(z.object({ id: z.number(), memo: z.string().min(1), amount: z.number(), accountId: z.number() }))
        .mutation(({ ctx, input }) => {
        return ctx.db.transactions.update({
            where: {
                id: input.id,
            },
            data: {
                memo: input.memo,
                amount: input.amount,
                accountId: input.accountId,
                transactionDate: new Date() // Add the transactionDate property
            },
        });
    }),

    delete: publicProcedure
        .input(z.object({ id: z.number() }))
        .mutation(({ ctx, input }) => {
        return ctx.db.transactions.delete({
            where: {
                id: input.id,
            },
        });
    }),

    getByAccountId: publicProcedure
        .input(z.object({ accountId: z.number() }))
        .query(({ ctx, input }) => {
        return ctx.db.transactions.findMany({
            where: {
                accountId: input.accountId
            }
        });
    })
});
